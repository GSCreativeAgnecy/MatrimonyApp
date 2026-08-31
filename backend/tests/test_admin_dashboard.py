from app.db.enums import UserRole
from tests.conftest import auth_headers, register_user, unique_email
from tests.test_admin_permissions import promote


class TestDashboard:
    async def test_summary(self, client, session_factory):
        tokens = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.get("/api/v1/admin/dashboard/summary", headers=auth_headers(tokens))
        assert resp.status_code == 200
        data = resp.json()["data"]
        for key in [
            "total_users",
            "new_users_today",
            "active_users_today",
            "new_matches_today",
            "pending_verifications",
            "open_reports",
            "today_revenue",
            "active_premium_subscriptions",
        ]:
            assert key in data

    async def test_summary_counts_users(self, client, session_factory):
        await register_user(client, email=unique_email())
        await register_user(client, email=unique_email())
        tokens = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.get("/api/v1/admin/dashboard/summary", headers=auth_headers(tokens))
        assert resp.json()["data"]["total_users"] >= 3

    async def test_action_center(self, client, session_factory):
        tokens = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.get("/api/v1/admin/dashboard/action-center", headers=auth_headers(tokens))
        assert resp.status_code == 200
        items = {i["key"]: i for i in resp.json()["data"]}
        assert set(items) == {"pending_verifications", "open_reports", "failed_payments", "job_verification_queue"}

    async def test_recent_activity(self, client, session_factory):
        await register_user(client)
        tokens = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.get("/api/v1/admin/dashboard/recent-activity", headers=auth_headers(tokens))
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)

    async def test_timeseries_endpoints(self, client, session_factory):
        tokens = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        for path in ["user-growth", "engagement", "revenue", "moderation"]:
            resp = await client.get(f"/api/v1/admin/dashboard/{path}?range=7d", headers=auth_headers(tokens))
            assert resp.status_code == 200, path
            assert isinstance(resp.json()["data"], list)

    async def test_analyst_can_read_dashboard(self, client, session_factory):
        tokens = await promote(client, session_factory, unique_email("an"), UserRole.ANALYST)
        resp = await client.get("/api/v1/admin/dashboard/summary", headers=auth_headers(tokens))
        assert resp.status_code == 200

    async def test_user_forbidden(self, client):
        tokens = await register_user(client)
        resp = await client.get("/api/v1/admin/dashboard/summary", headers=auth_headers(tokens))
        assert resp.status_code == 403
