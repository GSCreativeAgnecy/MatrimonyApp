from tests.conftest import register_user


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
        )
        assert resp.status_code == 200

    async def test_unknown_provider_rejected(self, client):
        resp = await client.post(
            "/api/v1/payments/webhook/unknown",
            json=_webhook_payload("x", "SUCCESS"),
        )
        assert resp.status_code == 401


def _uid_from_token(tokens: dict) -> str:
    import jwt

    from app.config.settings import settings

    return jwt.decode(tokens["access_token"], settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])["sub"]
