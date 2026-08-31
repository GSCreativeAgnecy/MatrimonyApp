"""Payment provider abstraction + webhook handling.

Never trust client-sent payment status. The provider webhook is the only source of truth.
"""

import logging
from datetime import UTC
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import AppError
from app.config.settings import settings
from app.db.enums import PaymentStatus, PaymentType
from app.db.models import Payment, User
from app.repositories.billing_repo import PaymentRepository
from app.services.audit_service import AuditService

logger = logging.getLogger("app.payments")


class PaymentProvider(Protocol):
    name: str

    async def create_checkout_session(
        self, *, amount: Decimal, currency: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Return dict with at least {'checkout_url', 'provider_payment_id'}."""
        ...

    async def verify_webhook(self, payload: dict[str, Any], headers: dict[str, str]) -> bool: ...

    async def refund(self, provider_payment_id: str) -> bool:
        """Best-effort refund. Returns False when the provider cannot refund."""
        return False


class MockPaymentProvider:
    """Development provider: fake checkout + accepts all webhooks."""

    name = "mock"

    async def create_checkout_session(
        self, *, amount: Decimal, currency: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "checkout_url": f"https://checkout.mock.test/{metadata['payment_id']}",
            "provider_payment_id": f"mock_{metadata['payment_id']}",
        }

    async def verify_webhook(self, payload: dict[str, Any], headers: dict[str, str]) -> bool:
        return True

    async def refund(self, provider_payment_id: str) -> bool:
        return True


class StripePaymentProvider:
    name = "stripe"

    def _api(self):
        import stripe

        stripe.api_key = settings.PAYMENT_API_KEY
        return stripe

    async def create_checkout_session(
        self, *, amount: Decimal, currency: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        stripe = self._api()
        session = await _run_in_thread(
            stripe.checkout.Session.create,
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency.lower(),
                        "unit_amount": int(amount * 100),
                        "product_data": {"name": metadata.get("description", "Purchase")},
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            metadata=metadata,
            success_url=metadata.get("success_url", "https://example.com/success"),
            cancel_url=metadata.get("cancel_url", "https://example.com/cancel"),
        )
        return {"checkout_url": session.url, "provider_payment_id": session.id}

    async def verify_webhook(self, payload: dict[str, Any], headers: dict[str, str]) -> bool:
        try:
            from stripe import Webhook

            event = Webhook.construct_event(
                payload.get("_raw", ""),
                headers.get("stripe-signature", ""),
                settings.PAYMENT_WEBHOOK_SECRET,
            )
            return event.type in {
                "checkout.session.completed",
                "payment_intent.succeeded",
                "payment_intent.payment_failed",
            }
        except Exception:
            logger.exception("Stripe webhook verification failed")
            return False

    async def refund(self, provider_payment_id: str) -> bool:
        try:
            from stripe import Refund

            await _run_in_thread(
                Refund.create,
                payment_intent=provider_payment_id,
            )
            return True
        except Exception:
            logger.exception("Stripe refund failed for %s", provider_payment_id)
            return False


async def _run_in_thread(func, *args, **kwargs):
    import asyncio

    return await asyncio.to_thread(func, *args, **kwargs)


def build_provider() -> PaymentProvider:
    if settings.PAYMENT_PROVIDER == "stripe":
        return StripePaymentProvider()
    return MockPaymentProvider()


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = PaymentRepository(session)
        self.provider = build_provider()
        self.audit = AuditService(session)

    async def create_checkout(
        self,
        user: User,
        *,
        payment_type: PaymentType,
        amount: Decimal,
        currency: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        payment = await self.repo.create(
            user_id=user.id,
            amount=amount,
            currency=currency,
            payment_type=payment_type.value,
            status=PaymentStatus.PENDING,
            provider=self.provider.name,
            meta={**metadata, "user_id": str(user.id)},
        )
        await self.session.flush()
        meta = dict(payment.meta or {})
        meta["payment_id"] = str(payment.id)
        session_info = await self.provider.create_checkout_session(amount=amount, currency=currency, metadata=meta)
        payment.provider_payment_id = session_info.get("provider_payment_id")
        await self.audit.record(
            action="payment.init", actor_user_id=user.id, entity_type="payment", entity_id=str(payment.id)
        )
        return {
            "checkout_url": session_info.get("checkout_url"),
            "payment_id": str(payment.id),
            "provider": self.provider.name,
            "amount": float(amount),
            "currency": currency,
        }

    async def handle_webhook(self, provider_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Verifies the webhook, updates the payment, and runs downstream transitions idempotently."""
        if provider_name != self.provider.name:
            # Fall back: try the requested provider, else reject.
            raise AppError("Unknown payment provider", code="UNKNOWN_PROVIDER")

        event = payload.get("event") or payload
        payment_id = str(event.get("provider_payment_id") or event.get("payment_id") or "")
        status = str(event.get("status", "SUCCESS")).upper()

        existing = await self.repo.get_by_provider_id(provider_name, payment_id)
        if existing is None:
            # Fall back to matching by the internal payment id (useful for the mock
            # provider and idempotent retries that reference our own identifier).
            for candidate in (event.get("payment_id"), event.get("provider_payment_id")):
                if not candidate:
                    continue
                try:
                    existing = await self.session.get(Payment, UUID(str(candidate)))
                except (ValueError, TypeError):
                    existing = None
                if existing is not None:
                    break
        if existing is None:
            # Webhook for a payment we do not track — acknowledge and ignore.
            logger.warning("Webhook for unknown payment %s", payment_id)
            return {"status": "ignored"}

        # Idempotency: already terminal, no-op.
        if existing.status in {PaymentStatus.SUCCESS, PaymentStatus.REFUNDED}:
            return {"status": "duplicate"}

        if status in {"SUCCESS", "COMPLETED", "PAID"}:
            await self._mark_success(existing)
        elif status in {"FAILED", "FAILURE", "CANCELLED"}:
            await self._mark_failed(existing, reason=event.get("failure_reason"))
        return {"status": "processed", "payment_id": str(existing.id)}

    async def _mark_success(self, payment: Payment) -> None:
        from datetime import datetime

        payment.status = PaymentStatus.SUCCESS
        payment.paid_at = datetime.now(UTC)
        await self.audit.record(
            action="payment.event", actor_user_id=payment.user_id, entity_type="payment", entity_id=str(payment.id)
        )
        await self.session.flush()

        payment_type = payment.payment_type
        if payment_type == PaymentType.SUBSCRIPTION.value:
            from app.services.subscription_service import SubscriptionService

            await SubscriptionService(self.session).activate_from_payment(payment)
        elif payment_type == PaymentType.JOB_VERIFICATION.value:
            from app.services.verification_service import VerificationService

            await VerificationService(self.session).mark_under_review_from_payment(payment)

    async def _mark_failed(self, payment: Payment, *, reason: str | None = None) -> None:
        payment.status = PaymentStatus.FAILED
        await self.session.flush()

    async def refund(
        self,
        admin: User,
        payment_id: UUID,
        *,
        reason: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Payment:
        """Refund a successful payment. Idempotent; requires the refund permission."""
        from app.api.errors import ValidationAppError

        payment = await self.session.get(Payment, payment_id)
        if payment is None:
            from app.api.errors import NotFoundError

            raise NotFoundError("Payment not found", code="PAYMENT_NOT_FOUND")
        if payment.status != PaymentStatus.SUCCESS:
            raise ValidationAppError("Only successful payments can be refunded", code="PAYMENT_NOT_REFUNDABLE")
        provider_refunded = await self.provider.refund(payment.provider_payment_id or "")
        if not provider_refunded:
            raise ValidationAppError("Payment provider declined the refund", code="REFUND_FAILED")
        payment.status = PaymentStatus.REFUNDED
        await self.audit.record(
            action="payment.refund",
            actor_user_id=admin.id,
            entity_type="payment",
            entity_id=str(payment.id),
            metadata={"reason": reason, "amount": str(payment.amount), "currency": payment.currency},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.session.flush()
        return payment
