"""Payment provider abstraction + webhook handling.

Never trust client-sent payment status. The provider webhook is the only source of truth.
"""

import json
import logging
import secrets
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

    async def parse_webhook(self, raw_body: bytes, headers: dict[str, str]) -> dict[str, Any] | None:
        """Verify a webhook request and return a normalized event, or None when invalid.

        Normalized shape: ``{"provider_payment_id", "payment_id", "status", "failure_reason"}``.
        """
        ...

    async def refund(self, provider_payment_id: str) -> bool:
        """Best-effort refund. Returns False when the provider cannot refund."""
        return False


def _normalize_event(
    *,
    provider_payment_id: str | None,
    payment_id: str | None,
    status: str,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "provider_payment_id": provider_payment_id,
        "payment_id": payment_id,
        "status": status.upper(),
        "failure_reason": failure_reason,
    }


class MockPaymentProvider:
    """Development provider: fake checkout + webhooks gated by a shared secret header.

    The webhook secret is required so the mock provider can never be used to
    activate payments without holding the server-side secret, even if the mock
    provider is explicitly allowed outside development.
    """

    name = "mock"
    SECRET_HEADER = "x-mock-webhook-secret"

    async def create_checkout_session(
        self, *, amount: Decimal, currency: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "checkout_url": f"https://checkout.mock.test/{metadata['payment_id']}",
            "provider_payment_id": f"mock_{metadata['payment_id']}",
        }

    async def parse_webhook(self, raw_body: bytes, headers: dict[str, str]) -> dict[str, Any] | None:
        provided = headers.get(self.SECRET_HEADER, "")
        expected = settings.PAYMENT_WEBHOOK_SECRET
        if not provided or not expected or not secrets.compare_digest(provided, expected):
            logger.warning("Mock webhook rejected: missing/invalid %s header", self.SECRET_HEADER)
            return None
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None
        event = payload.get("event") or payload
        return _normalize_event(
            provider_payment_id=str(event.get("provider_payment_id") or "") or None,
            payment_id=str(event.get("payment_id") or "") or None,
            status=str(event.get("status", "SUCCESS")),
            failure_reason=event.get("failure_reason"),
        )

    async def refund(self, provider_payment_id: str) -> bool:
        return True


class StripePaymentProvider:
    name = "stripe"

    _SUCCESS_EVENTS = {"checkout.session.completed", "payment_intent.succeeded"}
    _FAILURE_EVENTS = {"payment_intent.payment_failed", "checkout.session.expired"}

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

    async def parse_webhook(self, raw_body: bytes, headers: dict[str, str]) -> dict[str, Any] | None:
        if not raw_body:
            return None
        try:
            from stripe import Webhook

            event = Webhook.construct_event(
                raw_body,
                headers.get("stripe-signature", ""),
                settings.PAYMENT_WEBHOOK_SECRET,
            )
        except Exception:
            logger.exception("Stripe webhook verification failed")
            return None

        event_type = event.get("type", "")
        if event_type not in self._SUCCESS_EVENTS | self._FAILURE_EVENTS:
            return None

        obj = (event.get("data") or {}).get("object") or {}
        metadata = obj.get("metadata") or {}
        status = "SUCCESS" if event_type in self._SUCCESS_EVENTS else "FAILED"
        failure_reason = None
        if status == "FAILED":
            last_error = obj.get("last_payment_error") or {}
            failure_reason = last_error.get("message")
        return _normalize_event(
            provider_payment_id=str(obj.get("id") or "") or None,
            payment_id=str(metadata.get("payment_id") or "") or None,
            status=status,
            failure_reason=failure_reason,
        )

    async def refund(self, provider_payment_id: str) -> bool:
        try:
            from stripe import Refund

            if not provider_payment_id:
                return False
            payment_intent = provider_payment_id
            if provider_payment_id.startswith("cs_"):
                stripe = self._api()
                session = await _run_in_thread(stripe.checkout.Session.retrieve, provider_payment_id)
                payment_intent = session.get("payment_intent") or ""
                if not payment_intent:
                    return False
            await _run_in_thread(Refund.create, payment_intent=payment_intent)
            return True
        except Exception:
            logger.exception("Stripe refund failed for %s", provider_payment_id)
            return False


async def _run_in_thread(func, *args, **kwargs):
    import asyncio

    return await asyncio.to_thread(func, *args, **kwargs)


def build_provider() -> PaymentProvider:
    provider = (settings.PAYMENT_PROVIDER or "").strip().lower()
    if provider == "stripe":
        return StripePaymentProvider()
    if provider == "mock":
        return MockPaymentProvider()
    # Never silently fall back to the mock provider for an unknown name.
    raise AppError(f"Unsupported payment provider: {settings.PAYMENT_PROVIDER!r}", code="UNSUPPORTED_PROVIDER")


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

    async def handle_webhook(self, provider_name: str, event: dict[str, Any]) -> dict[str, Any]:
        """Applies an already-verified, normalized provider event idempotently."""
        if provider_name != self.provider.name:
            raise AppError("Unknown payment provider", code="UNKNOWN_PROVIDER")

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
