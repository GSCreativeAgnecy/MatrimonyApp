from app.config.settings import settings
from tests.conftest import register_user


def _webhook_headers(secret: str | None = None) -> dict:
    return {"x-mock-webhook-secret": secret if secret is not None else settings.PAYMENT_WEBHOOK_SECRET}


def _webhook_payload(payment_id: str, status: str = "SUCCESS") -> dict:
    return {
        "event": {
            "provider_payment_id": payment_id,
            "status": status,
        }
    }


class TestPaymentsWebhook:
    async def test_successful_webhook(self, client, session_factory):
        tokens = await register_user(client)

        async with session_factory() as session:
            from app.db.enums import PaymentStatus
            from app.services.payment_service import PaymentService

            payment = await PaymentService(session).repo.create(
                user_id=_uid_from_token(tokens),
                amount=100,
                currency="INR",
                payment_type="OTHER",
                status=PaymentStatus.PENDING,
                provider="mock",
                provider_payment_id="mock_abc",
                meta={},
            )
            await session.commit()

        resp = await client.post(
            "/api/v1/payments/webhook/mock",
            json=_webhook_payload("mock_abc", "SUCCESS"),
            headers=_webhook_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "processed"

    async def test_duplicate_webhook_idempotent(self, client, session_factory):
        tokens = await register_user(client)

        async with session_factory() as session:
            from app.db.enums import PaymentStatus
            from app.services.payment_service import PaymentService

            await PaymentService(session).repo.create(
                user_id=_uid_from_token(tokens),
                amount=100,
                currency="INR",
                payment_type="OTHER",
                status=PaymentStatus.SUCCESS,
                provider="mock",
                provider_payment_id="mock_dup",
                meta={},
            )
            await session.commit()

        resp = await client.post(
            "/api/v1/payments/webhook/mock",
            json=_webhook_payload("mock_dup", "SUCCESS"),
            headers=_webhook_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "duplicate"

    async def test_failed_webhook(self, client, session_factory):
        tokens = await register_user(client)

        async with session_factory() as session:
            from app.db.enums import PaymentStatus
            from app.services.payment_service import PaymentService

            await PaymentService(session).repo.create(
                user_id=_uid_from_token(tokens),
                amount=100,
                currency="INR",
                payment_type="OTHER",
                status=PaymentStatus.PENDING,
                provider="mock",
                provider_payment_id="mock_fail",
                meta={},
            )
            await session.commit()

        resp = await client.post(
            "/api/v1/payments/webhook/mock",
            json=_webhook_payload("mock_fail", "FAILED"),
            headers=_webhook_headers(),
        )
        assert resp.status_code == 200

    async def test_webhook_without_secret_rejected(self, client, session_factory):
        """The mock provider must not accept unauthenticated webhooks."""
        tokens = await register_user(client)

        async with session_factory() as session:
            from app.db.enums import PaymentStatus
            from app.services.payment_service import PaymentService

            await PaymentService(session).repo.create(
                user_id=_uid_from_token(tokens),
                amount=100,
                currency="INR",
                payment_type="OTHER",
                status=PaymentStatus.PENDING,
                provider="mock",
                provider_payment_id="mock_nosecret",
                meta={},
            )
            await session.commit()

        resp = await client.post(
            "/api/v1/payments/webhook/mock",
            json=_webhook_payload("mock_nosecret", "SUCCESS"),
        )
        assert resp.status_code == 401

        # ... and the payment must still be pending.
        async with session_factory() as session:
            from app.repositories.billing_repo import PaymentRepository

            payment = await PaymentRepository(session).get_by_provider_id("mock", "mock_nosecret")
            assert payment is not None
            assert payment.status.value == "PENDING"

    async def test_webhook_with_wrong_secret_rejected(self, client):
        resp = await client.post(
            "/api/v1/payments/webhook/mock",
            json=_webhook_payload("mock_abc", "SUCCESS"),
            headers=_webhook_headers(secret="wrong-secret"),
        )
        assert resp.status_code == 401

    async def test_unknown_provider_rejected(self, client):
        resp = await client.post(
            "/api/v1/payments/webhook/unknown",
            json=_webhook_payload("x", "SUCCESS"),
            headers=_webhook_headers(),
        )
        assert resp.status_code == 401


def _uid_from_token(tokens: dict) -> str:
    import jwt

    from app.config.settings import settings

    return jwt.decode(tokens["access_token"], settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])["sub"]
