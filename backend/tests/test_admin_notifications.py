from sqlalchemy import select

from app.db.enums import UserRole
from app.db.models import Notification
from tests.conftest import auth_headers, register_user, unique_email
from tests.test_admin_permissions import promote


class TestCampaigns:
    async def test_create_all_campaign(self, client, session_factory):
        await register_user(client)
        await register_user(client)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.post(
            "/api/v1/admin/notifications/campaign",
            headers=auth_headers(admin),
            json={
                "title": "Big Sale",
                "message": "Premium is 20% off",
                "channel": "PUSH",
                "audience": {"type": "all"},
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["status"] == "QUEUED"
        assert data["target_count"] == 3  # 2 users + the admin

    async def test_custom_audience(self, client, session_factory):
        user = await register_user(client)
        user_id = (await client.get("/api/v1/auth/me", headers=auth_headers(user))).json()["data"]["id"]
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.post(
            "/api/v1/admin/notifications/campaign",
            headers=auth_headers(admin),
            json={
                "title": "Hi",
                "message": "Hello there",
                "channel": "PUSH",
                "audience": {"type": "custom", "user_ids": [user_id]},
            },
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["target_count"] == 1

    async def test_worker_processes_campaign(self, client, session_factory):
        user = await register_user(client)
        user_id = (await client.get("/api/v1/auth/me", headers=auth_headers(user))).json()["data"]["id"]
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.post(
            "/api/v1/admin/notifications/campaign",
            headers=auth_headers(admin),
            json={
                "title": "Hi",
                "message": "Hello",
                "channel": "EMAIL",
                "audience": {"type": "custom", "user_ids": [user_id]},
            },
        )
        campaign_id = resp.json()["data"]["id"]

        # Simulate the ARQ worker fan-out.
        from app.services.notification_campaign_service import NotificationCampaignService

        async with session_factory() as session:
            result = await NotificationCampaignService(session).process(campaign_id)
            assert result["status"] == "done"
            rows = (await session.execute(select(Notification))).scalars().all()
            assert len(rows) == 1
            assert rows[0].title == "Hi"

    async def test_empty_audience_rejected(self, client, session_factory):
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.post(
            "/api/v1/admin/notifications/campaign",
            headers=auth_headers(admin),
            json={
                "title": "Hi",
                "message": "Hello",
                "channel": "PUSH",
                "audience": {"type": "custom", "user_ids": []},
            },
        )
        assert resp.status_code == 422

    async def test_invalid_audience_rejected(self, client, session_factory):
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.post(
            "/api/v1/admin/notifications/campaign",
            headers=auth_headers(admin),
            json={
                "title": "Hi",
                "message": "Hello",
                "channel": "PUSH",
                "audience": {"type": "planet"},
            },
        )
        assert resp.status_code == 422

    async def test_city_audience_needs_city(self, client, session_factory):
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.post(
            "/api/v1/admin/notifications/campaign",
            headers=auth_headers(admin),
            json={
                "title": "Hi",
                "message": "Hello",
                "channel": "PUSH",
                "audience": {"type": "city"},
            },
        )
        assert resp.status_code == 422

    async def test_campaigns_require_send_permission(self, client, session_factory):
        finance = await promote(client, session_factory, unique_email("fin"), UserRole.FINANCE)
        resp = await client.post(
            "/api/v1/admin/notifications/campaign",
            headers=auth_headers(finance),
            json={
                "title": "Hi",
                "message": "Hello",
                "channel": "PUSH",
                "audience": {"type": "all"},
            },
        )
        assert resp.status_code == 403

    async def test_list_campaigns(self, client, session_factory):
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        await client.post(
            "/api/v1/admin/notifications/campaign",
            headers=auth_headers(admin),
            json={"title": "Hi", "message": "Hello", "channel": "PUSH", "audience": {"type": "all"}},
        )
        resp = await client.get("/api/v1/admin/notifications/campaigns", headers=auth_headers(admin))
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1
