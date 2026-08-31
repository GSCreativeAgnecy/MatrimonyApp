from sqlalchemy import select

from app.db.enums import UserRole
from app.db.models import AuditLog
from tests.conftest import auth_headers, register_user, unique_email
from tests.test_admin_permissions import promote


class TestAdminUsersManagement:
    async def test_create_new_admin(self, client, session_factory):
        super_admin = await promote(client, session_factory, unique_email("sa"), UserRole.SUPER_ADMIN)
        email = unique_email("newadmin")
        resp = await client.post(
            "/api/v1/admin/admin-users",
            headers=auth_headers(super_admin),
            json={"email": email, "password": "Adminpass123", "role": "MODERATOR"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["role"] == "MODERATOR"

    async def test_promote_existing_user(self, client, session_factory):
        super_admin = await promote(client, session_factory, unique_email("sa"), UserRole.SUPER_ADMIN)
        email = unique_email()
        await register_user(client, email=email)
        resp = await client.post(
            "/api/v1/admin/admin-users",
            headers=auth_headers(super_admin),
            json={"email": email, "role": "SUPPORT"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["role"] == "SUPPORT"

    async def test_new_admin_without_password_422(self, client, session_factory):
        super_admin = await promote(client, session_factory, unique_email("sa"), UserRole.SUPER_ADMIN)
        resp = await client.post(
            "/api/v1/admin/admin-users",
            headers=auth_headers(super_admin),
            json={"email": unique_email("x"), "role": "MODERATOR"},
        )
        assert resp.status_code == 422

    async def test_list_admin_users(self, client, session_factory):
        super_admin = await promote(client, session_factory, unique_email("sa"), UserRole.SUPER_ADMIN)
        resp = await client.get("/api/v1/admin/admin-users", headers=auth_headers(super_admin))
        assert resp.status_code == 200
        roles = {r["role"] for r in resp.json()["data"]}
        assert "SUPER_ADMIN" in roles

    async def test_change_admin_role(self, client, session_factory):
        super_admin = await promote(client, session_factory, unique_email("sa"), UserRole.SUPER_ADMIN)
        mod_email = unique_email("mod")
        mod = await promote(client, session_factory, mod_email, UserRole.MODERATOR)
        mod_id = (await client.get("/api/v1/auth/me", headers=auth_headers(mod))).json()["data"]["id"]
        resp = await client.patch(
            f"/api/v1/admin/admin-users/{mod_id}/role",
            headers=auth_headers(super_admin),
            json={"role": "FINANCE"},
        )
        assert resp.status_code == 200
        detail = await client.get(f"/api/v1/admin/users/{mod_id}", headers=auth_headers(super_admin))
        assert detail.json()["data"]["role"] == "FINANCE"

    async def test_disable_admin_revokes_access(self, client, session_factory):
        super_admin = await promote(client, session_factory, unique_email("sa"), UserRole.SUPER_ADMIN)
        mod_email = unique_email("mod")
        mod = await promote(client, session_factory, mod_email, UserRole.MODERATOR)
        mod_id = (await client.get("/api/v1/auth/me", headers=auth_headers(mod))).json()["data"]["id"]
        resp = await client.post(
            f"/api/v1/admin/admin-users/{mod_id}/disable",
            headers=auth_headers(super_admin),
            json={"reason": "no longer needed"},
        )
        assert resp.status_code == 200
        # The disabled admin is locked out.
        login = await client.post("/api/v1/auth/login", json={"email": mod_email, "password": "Testpass123"})
        assert login.status_code == 401

    async def test_admin_cannot_disable_self(self, client, session_factory):
        super_admin = await promote(client, session_factory, unique_email("sa"), UserRole.SUPER_ADMIN)
        me = (await client.get("/api/v1/auth/me", headers=auth_headers(super_admin))).json()["data"]["id"]
        resp = await client.post(
            f"/api/v1/admin/admin-users/{me}/disable",
            headers=auth_headers(super_admin),
            json={"reason": "oops"},
        )
        assert resp.status_code == 403

    async def test_regular_admin_cannot_grant_super_admin(self, client, session_factory):
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        email = unique_email()
        await register_user(client, email=email)
        resp = await client.post(
            "/api/v1/admin/admin-users",
            headers=auth_headers(admin),
            json={"email": email, "role": "SUPER_ADMIN"},
        )
        assert resp.status_code == 403

    async def test_actions_are_audited(self, client, session_factory):
        super_admin = await promote(client, session_factory, unique_email("sa"), UserRole.SUPER_ADMIN)
        email = unique_email("newadmin")
        await client.post(
            "/api/v1/admin/admin-users",
            headers=auth_headers(super_admin),
            json={"email": email, "password": "Adminpass123", "role": "MODERATOR"},
        )
        async with session_factory() as session:
            rows = (
                (await session.execute(select(AuditLog).where(AuditLog.action == "admin.admin_created")))
                .scalars()
                .all()
            )
        assert len(rows) == 1
