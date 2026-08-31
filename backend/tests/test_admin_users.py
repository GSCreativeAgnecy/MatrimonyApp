from sqlalchemy import select

from app.db.enums import UserRole
from app.db.models import AuditLog, User
from tests.conftest import auth_headers, create_full_profile, register_user, unique_email
from tests.test_admin_permissions import promote


async def _target_id(client, tokens) -> str:
    return (await client.get("/api/v1/auth/me", headers=auth_headers(tokens))).json()["data"]["id"]


class TestUserList:
    async def test_list_paginated(self, client, session_factory):
        for _ in range(3):
            await register_user(client)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.get("/api/v1/admin/users?limit=2", headers=auth_headers(admin))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) <= 2
        assert resp.json()["meta"]["total"] >= 4

    async def test_filter_by_status(self, client, session_factory):
        banned = await register_user(client)
        banned_id = await _target_id(client, banned)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        await client.post(
            f"/api/v1/admin/users/{banned_id}/ban",
            headers=auth_headers(admin),
            json={"reason": "spam"},
        )
        resp = await client.get("/api/v1/admin/users?account_status=BANNED", headers=auth_headers(admin))
        ids = [r["id"] for r in resp.json()["data"]]
        assert banned_id in ids

    async def test_search_by_email(self, client, session_factory):
        email = unique_email("needle")
        await register_user(client, email=email)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.get(f"/api/v1/admin/users?search={email.split('@')[0]}", headers=auth_headers(admin))
        assert any(r["email"] == email for r in resp.json()["data"])

    async def test_premium_filter(self, client, session_factory):
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.get("/api/v1/admin/users?premium=true", headers=auth_headers(admin))
        assert resp.status_code == 200


class TestUserDetail:
    async def test_detail(self, client, session_factory):
        tokens = await register_user(client)
        await create_full_profile(client, tokens)
        user_id = await _target_id(client, tokens)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.get(f"/api/v1/admin/users/{user_id}", headers=auth_headers(admin))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["profile"]["first_name"] == "Anita"
        assert data["role"] == "USER"

    async def test_subresources(self, client, session_factory):
        tokens = await register_user(client)
        user_id = await _target_id(client, tokens)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        for path in ["profile", "photos", "verifications", "matches", "conversations", "payments", "reports", "audit"]:
            resp = await client.get(f"/api/v1/admin/users/{user_id}/{path}", headers=auth_headers(admin))
            assert resp.status_code == 200, path

    async def test_missing_user_404(self, client, session_factory):
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.get(
            "/api/v1/admin/users/00000000-0000-0000-0000-000000000000", headers=auth_headers(admin)
        )
        assert resp.status_code == 404


class TestUserActions:
    async def test_suspend_flow(self, client, session_factory):
        email = unique_email()
        target = await register_user(client, email=email)
        target_id = await _target_id(client, target)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.post(
            f"/api/v1/admin/users/{target_id}/suspend",
            headers=auth_headers(admin),
            json={"reason": "inappropriate", "duration_minutes": 60, "admin_notes": "temporary"},
        )
        assert resp.status_code == 200
        # The target is now locked out of the app.
        locked = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Testpass123"},
        )
        assert locked.status_code == 401

    async def test_ban_unban(self, client, session_factory):
        target = await register_user(client)
        target_id = await _target_id(client, target)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        await client.post(f"/api/v1/admin/users/{target_id}/ban", headers=auth_headers(admin), json={"reason": "scam"})
        detail = await client.get(f"/api/v1/admin/users/{target_id}", headers=auth_headers(admin))
        assert detail.json()["data"]["is_banned"] is True
        await client.post(f"/api/v1/admin/users/{target_id}/unban", headers=auth_headers(admin))
        detail = await client.get(f"/api/v1/admin/users/{target_id}", headers=auth_headers(admin))
        assert detail.json()["data"]["is_banned"] is False

    async def test_delete_and_restore(self, client, session_factory):
        target = await register_user(client)
        target_id = await _target_id(client, target)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.post(
            f"/api/v1/admin/users/{target_id}/delete",
            headers=auth_headers(admin),
            json={"reason": "duplicate account"},
        )
        assert resp.status_code == 200
        detail = await client.get(f"/api/v1/admin/users/{target_id}", headers=auth_headers(admin))
        assert detail.json()["data"]["account_status"] == "DELETED"
        await client.post(f"/api/v1/admin/users/{target_id}/restore", headers=auth_headers(admin))
        detail = await client.get(f"/api/v1/admin/users/{target_id}", headers=auth_headers(admin))
        assert detail.json()["data"]["account_status"] == "ACTIVE"

    async def test_verify(self, client, session_factory):
        target = await register_user(client)
        target_id = await _target_id(client, target)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.post(
            f"/api/v1/admin/users/{target_id}/verify", headers=auth_headers(admin), json={"kind": "email"}
        )
        assert resp.status_code == 200
        detail = await client.get(f"/api/v1/admin/users/{target_id}", headers=auth_headers(admin))
        assert detail.json()["data"]["email_verified"] is True

    async def test_suspend_requires_permission(self, client, session_factory):
        target = await register_user(client)
        target_id = await _target_id(client, target)
        analyst = await promote(client, session_factory, unique_email("an"), UserRole.ANALYST)
        resp = await client.post(
            f"/api/v1/admin/users/{target_id}/suspend",
            headers=auth_headers(analyst),
            json={"reason": "spam"},
        )
        assert resp.status_code == 403

    async def test_actions_are_audited(self, client, session_factory):
        target = await register_user(client)
        target_id = await _target_id(client, target)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        await client.post(f"/api/v1/admin/users/{target_id}/ban", headers=auth_headers(admin), json={"reason": "spam"})
        async with session_factory() as session:
            rows = (await session.execute(select(AuditLog).where(AuditLog.action == "admin.ban"))).scalars().all()
        assert len(rows) == 1
        assert rows[0].entity_id == target_id

    async def test_admin_cannot_ban_another_admin(self, client, session_factory):
        admin1 = await promote(client, session_factory, unique_email("a1"), UserRole.ADMIN)
        admin2_email = unique_email("a2")
        await promote(client, session_factory, admin2_email, UserRole.ADMIN)
        async with session_factory() as session:
            admin2 = (await session.execute(select(User).where(User.email == admin2_email))).scalar_one()
            admin2_id = str(admin2.id)
        resp = await client.post(
            f"/api/v1/admin/users/{admin2_id}/ban", headers=auth_headers(admin1), json={"reason": "spam"}
        )
        assert resp.status_code == 403

    async def test_role_change_guarded(self, client, session_factory):
        target = await register_user(client)
        target_id = await _target_id(client, target)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.post(
            f"/api/v1/admin/users/{target_id}/role", headers=auth_headers(admin), json={"role": "SUPER_ADMIN"}
        )
        assert resp.status_code == 403  # only SUPER_ADMIN can grant SUPER_ADMIN
        resp = await client.post(
            f"/api/v1/admin/users/{target_id}/role", headers=auth_headers(admin), json={"role": "SUPPORT"}
        )
        assert resp.status_code == 200
