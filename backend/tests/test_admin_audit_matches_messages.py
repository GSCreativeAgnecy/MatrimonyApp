from sqlalchemy import select

from app.db.enums import UserRole
from app.db.models import AuditLog
from tests.conftest import auth_headers, create_full_profile, register_user, unique_email
from tests.test_admin_permissions import promote


async def _make_match(client, a_tokens, b_tokens) -> None:
    """Two users swipe on each other -> match."""
    b_id = (await client.get("/api/v1/auth/me", headers=auth_headers(b_tokens))).json()["data"]["id"]
    await client.post(
        "/api/v1/swipes", headers=auth_headers(a_tokens), json={"target_user_id": b_id, "action": "LIKE"}
    )
    a_id = (await client.get("/api/v1/auth/me", headers=auth_headers(a_tokens))).json()["data"]["id"]
    await client.post(
        "/api/v1/swipes", headers=auth_headers(b_tokens), json={"target_user_id": a_id, "action": "LIKE"}
    )


class TestAuditLogs:
    async def test_list_and_filters(self, client, session_factory):
        await register_user(client)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.get("/api/v1/admin/audit-logs", headers=auth_headers(admin))
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1

        resp = await client.get("/api/v1/admin/audit-logs?action=auth.register", headers=auth_headers(admin))
        assert all(r["action"] == "auth.register" for r in resp.json()["data"])

    async def test_read_only(self, client, session_factory):
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        # No mutation endpoint exists.
        resp = await client.post("/api/v1/admin/audit-logs", headers=auth_headers(admin), json={})
        assert resp.status_code == 405

    async def test_analyst_can_read(self, client, session_factory):
        analyst = await promote(client, session_factory, unique_email("an"), UserRole.ANALYST)
        resp = await client.get("/api/v1/admin/audit-logs", headers=auth_headers(analyst))
        assert resp.status_code == 200

    async def test_user_forbidden(self, client):
        tokens = await register_user(client)
        resp = await client.get("/api/v1/admin/audit-logs", headers=auth_headers(tokens))
        assert resp.status_code == 403


class TestMatchesAdmin:
    async def test_search_by_user(self, client, session_factory):
        a = await register_user(client)
        await create_full_profile(client, a, gender="FEMALE")
        b = await register_user(client)
        await create_full_profile(client, b, gender="MALE")
        await _make_match(client, a, b)
        a_id = (await client.get("/api/v1/auth/me", headers=auth_headers(a))).json()["data"]["id"]
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.get(f"/api/v1/admin/matches?user_id={a_id}", headers=auth_headers(admin))
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    async def test_match_detail(self, client, session_factory):
        a = await register_user(client)
        await create_full_profile(client, a, gender="FEMALE")
        b = await register_user(client)
        await create_full_profile(client, b, gender="MALE")
        await _make_match(client, a, b)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        matches = await client.get("/api/v1/admin/matches", headers=auth_headers(admin))
        match_id = matches.json()["data"][0]["id"]
        resp = await client.get(f"/api/v1/admin/matches/{match_id}", headers=auth_headers(admin))
        assert resp.status_code == 200


class TestMessagesAdmin:
    async def _setup_conversation(self, client):
        a = await register_user(client)
        await create_full_profile(client, a, gender="FEMALE")
        b = await register_user(client)
        await create_full_profile(client, b, gender="MALE")
        await _make_match(client, a, b)
        b_id = (await client.get("/api/v1/auth/me", headers=auth_headers(b))).json()["data"]["id"]
        conv = await client.post("/api/v1/conversations", headers=auth_headers(a), json={"user_id": b_id})
        conv_id = conv.json()["data"]["id"]
        await client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            headers=auth_headers(a),
            json={"body": "hello there"},
        )
        return conv_id

    async def test_conversation_search(self, client, session_factory):
        await self._setup_conversation(client)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.get("/api/v1/admin/messages/conversations", headers=auth_headers(admin))
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    async def test_private_view_audited(self, client, session_factory):
        conv_id = await self._setup_conversation(client)
        moderator = await promote(client, session_factory, unique_email("mod"), UserRole.MODERATOR)
        resp = await client.get(f"/api/v1/admin/messages/conversations/{conv_id}", headers=auth_headers(moderator))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["audited"] is True
        assert len(data["messages"]) == 1
        assert data["messages"][0]["body"] == "hello there"

        async with session_factory() as session:
            rows = (
                (await session.execute(select(AuditLog).where(AuditLog.action == "admin.message_view")))
                .scalars()
                .all()
            )
        assert len(rows) == 1
        assert rows[0].entity_id == conv_id

    async def test_private_view_requires_permission(self, client, session_factory):
        conv_id = await self._setup_conversation(client)
        finance = await promote(client, session_factory, unique_email("fin"), UserRole.FINANCE)
        resp = await client.get(f"/api/v1/admin/messages/conversations/{conv_id}", headers=auth_headers(finance))
        assert resp.status_code == 403
