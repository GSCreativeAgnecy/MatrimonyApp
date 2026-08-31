from sqlalchemy import select

from app.db.enums import UserRole
from app.db.models import JobVerification, User
from tests.conftest import auth_headers, create_full_profile, register_user, unique_email


class TestJobVerification:
    async def test_submit_job_verification(self, client):
        tokens = await register_user(client)
        await create_full_profile(client, tokens, gender="FEMALE")
        resp = await client.post(
            "/api/v1/verifications/job",
            headers=auth_headers(tokens),
            json={
                "employment_type": "LOCAL",
                "employer_name": "Acme Corp",
                "job_title": "Engineer",
                "country": "India",
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["verification_id"]
        assert data["amount"] == 119  # config-driven LOCAL price

    async def test_list_my_verifications(self, client):
        tokens = await register_user(client)
        await create_full_profile(client, tokens, gender="FEMALE")
        await client.post(
            "/api/v1/verifications/job",
            headers=auth_headers(tokens),
            json={"employment_type": "NRI", "employer_name": "Acme US", "country": "USA"},
        )
        resp = await client.get("/api/v1/verifications", headers=auth_headers(tokens))
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1
        assert resp.json()["data"][0]["verification_status"] == "PENDING_PAYMENT"


class TestAdminReview:
    async def test_regular_user_cannot_review(self, client):
        tokens = await register_user(client)
        await create_full_profile(client, tokens, gender="FEMALE")
        resp = await client.post(
            "/api/v1/verifications/job",
            headers=auth_headers(tokens),
            json={"employment_type": "LOCAL", "employer_name": "Acme"},
        )
        verification_id = resp.json()["data"]["verification_id"]

        resp = await client.post(
            f"/api/v1/admin/verifications/job/{verification_id}/review",
            headers=auth_headers(tokens),
            json={"approve": True},
        )
        assert resp.status_code == 401 or resp.status_code == 403

    async def test_admin_approval_flow(self, client, session_factory):
        # Register a user then promote them to ADMIN (simulating an admin seed).
        admin_email = unique_email("admin")
        admin_tokens = await register_user(client, email=admin_email)

        async with session_factory() as session:
            admin = (await session.execute(select(User).where(User.email == admin_email))).scalar_one()
            admin.role = UserRole.ADMIN
            await session.commit()

        # A regular user submits a paid job verification.
        tokens = await register_user(client)
        await create_full_profile(client, tokens, gender="FEMALE")
        resp = await client.post(
            "/api/v1/verifications/job",
            headers=auth_headers(tokens),
            json={"employment_type": "LOCAL", "employer_name": "Acme"},
        )
        verification_id = resp.json()["data"]["verification_id"]

        # Pay for it via a mock provider webhook.
        async with session_factory() as session:
            verification = (
                await session.execute(select(JobVerification).where(JobVerification.id == verification_id))
            ).scalar_one()
            payment_id = str(verification.payment_id)
            await client.post(
                "/api/v1/payments/webhook/mock",
                json={"event": {"provider_payment_id": payment_id, "status": "SUCCESS"}},
            )

        resp = await client.get("/api/v1/verifications", headers=auth_headers(tokens))
        assert resp.json()["data"][0]["verification_status"] == "UNDER_REVIEW"

        # Admin approves.
        resp = await client.post(
            f"/api/v1/admin/verifications/job/{verification_id}/review",
            headers=auth_headers(admin_tokens),
            json={"approve": True},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["verification_status"] == "VERIFIED"
