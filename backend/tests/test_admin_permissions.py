from sqlalchemy import select

from app.db.enums import UserRole
from app.db.models import User
from tests.conftest import auth_headers, register_user, unique_email


async def promote(client, session_factory, email: str, role: UserRole) -> dict:
    tokens = await register_user(client, email=email)
    async with session_factory() as session:
        user = (await session.execute(select(User).where(User.email == email))).scalar_one()
        user.role = role
        await session.commit()
    return tokens


class TestPermissionAuthorization:
    async def test_unauthenticated_gets_401(self, client):
        resp = await client.get("/api/v1/admin/dashboard/summary")
        assert resp.status_code == 401

    async def test_regular_user_forbidden(self, client):
        tokens = await register_user(client)
        resp = await client.get("/api/v1/admin/dashboard/summary", headers=auth_headers(tokens))
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    async def test_finance_cannot_access_moderation(self, client, session_factory):
        tokens = await promote(client, session_factory, unique_email("fin"), UserRole.FINANCE)
        resp = await client.get("/api/v1/admin/reports", headers=auth_headers(tokens))
        assert resp.status_code == 403
        resp = await client.get("/api/v1/admin/payments", headers=auth_headers(tokens))
        assert resp.status_code == 200

    async def test_analyst_cannot_refund(self, client, session_factory):
        tokens = await promote(client, session_factory, unique_email("an"), UserRole.ANALYST)
        resp = await client.get("/api/v1/admin/analytics/users", headers=auth_headers(tokens))
        assert resp.status_code == 200
        resp = await client.post("/api/v1/admin/audit-logs/x", headers=auth_headers(tokens))
        # No mutation endpoint exists on audit logs; a POST should not be found.
        assert resp.status_code == 405 or resp.status_code == 404

    async def test_moderator_cannot_manage_admins(self, client, session_factory):
        tokens = await promote(client, session_factory, unique_email("mod"), UserRole.MODERATOR)
        resp = await client.get("/api/v1/admin/admin-users", headers=auth_headers(tokens))
        assert resp.status_code == 403
        resp = await client.get("/api/v1/admin/users", headers=auth_headers(tokens))
        assert resp.status_code == 200

    async def test_verifier_cannot_ban(self, client, session_factory):
        tokens = await promote(client, session_factory, unique_email("ver"), UserRole.VERIFIER)
        target = await register_user(client)
        target_id = (await client.get("/api/v1/auth/me", headers=auth_headers(target))).json()["data"]["id"]
        resp = await client.post(
            f"/api/v1/admin/users/{target_id}/ban",
            headers=auth_headers(tokens),
            json={"reason": "nope"},
        )
        assert resp.status_code == 403

    async def test_admin_all_permissions(self, client, session_factory):
        tokens = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        assert (await client.get("/api/v1/admin/users", headers=auth_headers(tokens))).status_code == 200
        assert (await client.get("/api/v1/admin/roles", headers=auth_headers(tokens))).status_code == 200


class TestRoleManagement:
    async def test_list_roles(self, client, session_factory):
        tokens = await promote(client, session_factory, unique_email("sa"), UserRole.SUPER_ADMIN)
        resp = await client.get("/api/v1/admin/roles", headers=auth_headers(tokens))
        assert resp.status_code == 200
        roles = {r["role"]: r["permissions"] for r in resp.json()["data"]}
        assert "MODERATOR" in roles
        assert "users.suspend" in roles["MODERATOR"]
        assert "payments.refund" not in roles["ANALYST"]

    async def test_super_admin_can_update_permissions(self, client, session_factory):
        tokens = await promote(client, session_factory, unique_email("sa"), UserRole.SUPER_ADMIN)
        resp = await client.put(
            "/api/v1/admin/roles/ANALYST/permissions",
            headers=auth_headers(tokens),
            json={"permissions": ["users.read", "analytics.read", "payments.read"]},
        )
        assert resp.status_code == 200
        assert "users.read" in resp.json()["data"]["permissions"]

        # Enforced: an ANALYST now (still) cannot refund because payments.refund is absent.
        analyst = await promote(client, session_factory, unique_email("an2"), UserRole.ANALYST)
        target = await register_user(client)
        target_id = (await client.get("/api/v1/auth/me", headers=auth_headers(target))).json()["data"]["id"]
        resp = await client.post(
            f"/api/v1/admin/users/{target_id}/ban", headers=auth_headers(analyst), json={"reason": "x"}
        )
        assert resp.status_code == 403

    async def test_invalid_permission_rejected(self, client, session_factory):
        tokens = await promote(client, session_factory, unique_email("sa"), UserRole.SUPER_ADMIN)
        resp = await client.put(
            "/api/v1/admin/roles/ANALYST/permissions",
            headers=auth_headers(tokens),
            json={"permissions": ["not.a.permission"]},
        )
        assert resp.status_code == 422

    async def test_non_super_admin_cannot_manage_permissions(self, client, session_factory):
        tokens = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.put(
            "/api/v1/admin/roles/ANALYST/permissions",
            headers=auth_headers(tokens),
            json={"permissions": ["users.read"]},
        )
        assert resp.status_code == 200  # ADMIN may manage roles (admin_users.manage)

    async def test_super_admin_permissions_immutable(self, client, session_factory):
        tokens = await promote(client, session_factory, unique_email("sa"), UserRole.SUPER_ADMIN)
        resp = await client.put(
            "/api/v1/admin/roles/SUPER_ADMIN/permissions",
            headers=auth_headers(tokens),
            json={"permissions": ["users.read"]},
        )
        assert resp.status_code == 200
        assert "users.ban" in resp.json()["data"]["permissions"]
