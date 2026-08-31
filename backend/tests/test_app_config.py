import json

from sqlalchemy import select

from app.db.enums import UserRole
from app.db.models import AuditLog, User
from tests.conftest import auth_headers, create_full_profile, register_user, unique_email


class _FakeRedis:
    """Minimal in-memory Redis stub used to exercise the caching paths."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def setex(self, key: str, seconds: int, value: str) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


async def _promote(client, session_factory, email: str, role: UserRole) -> dict:
    tokens = await register_user(client, email=email)
    async with session_factory() as session:
        user = (await session.execute(select(User).where(User.email == email))).scalar_one()
        user.role = role
        await session.commit()
    return tokens


def _public(client, **kwargs):
    return client.get("/api/v1/app/config", **kwargs)


class TestPublicAPI:
    async def test_no_auth_required(self, client):
        resp = await client.get("/api/v1/app/config")
        assert resp.status_code == 200
        assert resp.json()["data"] is not None

    async def test_sensible_defaults_when_empty(self, client):
        resp = await client.get("/api/v1/app/config")
        data = resp.json()["data"]
        assert data["branding"]["app_name"] is None
        assert data["app"]["maintenance_mode"] is False
        assert data["features"]["registration"] is True
        assert data["versions"]["force_update_ios"] is False

    async def test_public_config_returned(self, client, session_factory):
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={
                "key": "branding.app_name",
                "value": "MyMatrimony",
                "value_type": "STRING",
                "category": "BRANDING",
                "is_public": True,
                "is_active": True,
            },
        )
        await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={
                "key": "features.enable_video_calls",
                "value": True,
                "value_type": "BOOLEAN",
                "category": "FEATURES",
                "is_public": True,
            },
        )
        await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={
                "key": "limits.max_photos",
                "value": 6,
                "value_type": "INTEGER",
                "category": "LIMITS",
                "is_public": True,
            },
        )

        resp = await _public(client)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["branding"]["app_name"] == "MyMatrimony"
        assert data["features"]["video_calls"] is True
        assert data["limits"]["max_photos"] == 6
        assert "version" in resp.json()["meta"]

    async def test_private_and_inactive_excluded(self, client, session_factory):
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={
                "key": "app.internal_flag",
                "value": "secret",
                "value_type": "STRING",
                "category": "APP",
                "is_public": False,
            },
        )
        await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={
                "key": "branding.tagline",
                "value": "Old",
                "value_type": "STRING",
                "category": "BRANDING",
                "is_active": False,
            },
        )

        resp = await _public(client)
        data = resp.json()["data"]
        assert "internal_flag" not in data["app"]
        # Inactive entries are not served; schema defaults keep the key stable at null.
        assert data["branding"]["tagline"] is None

    async def test_version_changes_when_public_config_changes(self, client, session_factory):
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={"key": "branding.app_name", "value": "One", "value_type": "STRING", "category": "BRANDING"},
        )
        v1 = (await _public(client)).json()["meta"]["version"]

        await client.patch(
            "/api/v1/admin/app-config/branding.app_name",
            headers=auth_headers(admin_tokens),
            json={"value": "Two"},
        )
        v2 = (await _public(client)).json()["meta"]["version"]
        assert v1 != v2


class TestAdminAuthorization:
    @staticmethod
    async def _setup(client, session_factory, role: UserRole) -> dict:
        return await _promote(client, session_factory, unique_email("admin"), role)

    async def test_user_forbidden(self, client):
        tokens = await register_user(client)
        resp = await client.get("/api/v1/admin/app-config", headers=auth_headers(tokens))
        assert resp.status_code == 403

    async def test_moderator_forbidden(self, client, session_factory):
        tokens = await self._setup(client, session_factory, UserRole.MODERATOR)
        resp = await client.get("/api/v1/admin/app-config", headers=auth_headers(tokens))
        assert resp.status_code == 403

    async def test_verifier_forbidden(self, client, session_factory):
        tokens = await self._setup(client, session_factory, UserRole.VERIFIER)
        resp = await client.get("/api/v1/admin/app-config", headers=auth_headers(tokens))
        assert resp.status_code == 403

    async def test_admin_allowed(self, client, session_factory):
        tokens = await self._setup(client, session_factory, UserRole.ADMIN)
        resp = await client.get("/api/v1/admin/app-config", headers=auth_headers(tokens))
        assert resp.status_code == 200

    async def test_super_admin_allowed(self, client, session_factory):
        tokens = await self._setup(client, session_factory, UserRole.SUPER_ADMIN)
        resp = await client.get("/api/v1/admin/app-config", headers=auth_headers(tokens))
        assert resp.status_code == 200


class TestAdminCrud:
    async def test_create_and_get(self, client, session_factory):
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        resp = await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={"key": "branding.app_name", "value": "MyMatrimony", "value_type": "STRING", "category": "BRANDING"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()["data"]
        assert body["key"] == "branding.app_name"
        assert body["value"] == "MyMatrimony"
        assert body["value_type"] == "STRING"
        assert body["category"] == "BRANDING"
        assert body["is_public"] is True

        resp = await client.get("/api/v1/admin/app-config/branding.app_name", headers=auth_headers(admin_tokens))
        assert resp.status_code == 200
        assert resp.json()["data"]["value"] == "MyMatrimony"

    async def test_list_with_filters(self, client, session_factory):
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={"key": "branding.app_name", "value": "A", "value_type": "STRING", "category": "BRANDING"},
        )
        await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={"key": "features.enable_premium", "value": True, "value_type": "BOOLEAN", "category": "FEATURES"},
        )

        resp = await client.get("/api/v1/admin/app-config?category=BRANDING", headers=auth_headers(admin_tokens))
        assert resp.status_code == 200
        keys = [r["key"] for r in resp.json()["data"]]
        assert keys == ["branding.app_name"]

        resp = await client.get("/api/v1/admin/app-config?is_active=false", headers=auth_headers(admin_tokens))
        assert resp.json()["data"] == []

    async def test_update(self, client, session_factory):
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={"key": "branding.app_name", "value": "One", "value_type": "STRING", "category": "BRANDING"},
        )
        resp = await client.patch(
            "/api/v1/admin/app-config/branding.app_name",
            headers=auth_headers(admin_tokens),
            json={"value": "Two", "is_public": False, "description": "renamed"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["value"] == "Two"
        assert data["is_public"] is False
        assert data["description"] == "renamed"

    async def test_deactivate_via_delete(self, client, session_factory):
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={"key": "branding.tagline", "value": "Hi", "value_type": "STRING", "category": "BRANDING"},
        )
        resp = await client.delete("/api/v1/admin/app-config/branding.tagline", headers=auth_headers(admin_tokens))
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "deactivated"

        row = await client.get("/api/v1/admin/app-config/branding.tagline", headers=auth_headers(admin_tokens))
        assert row.json()["data"]["is_active"] is False

        # Deactivated config must disappear from the public payload.
        public = (await _public(client)).json()["data"]
        assert public["branding"]["tagline"] is None

    async def test_duplicate_key_conflict(self, client, session_factory):
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        payload = {"key": "branding.app_name", "value": "A", "value_type": "STRING", "category": "BRANDING"}
        assert (
            await client.post("/api/v1/admin/app-config", headers=auth_headers(admin_tokens), json=payload)
        ).status_code == 200
        resp = await client.post("/api/v1/admin/app-config", headers=auth_headers(admin_tokens), json=payload)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "CONFIG_KEY_EXISTS"

    async def test_missing_key_404(self, client, session_factory):
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        resp = await client.get("/api/v1/admin/app-config/nope.missing", headers=auth_headers(admin_tokens))
        assert resp.status_code == 404

    async def test_invalid_value_type(self, client, session_factory):
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        resp = await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={"key": "limits.max_photos", "value": "six", "value_type": "INTEGER", "category": "LIMITS"},
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "INVALID_CONFIG_VALUE"

    async def test_invalid_color(self, client, session_factory):
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        resp = await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={"key": "branding.primary_color", "value": "red", "value_type": "STRING", "category": "BRANDING"},
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "INVALID_COLOR"

    async def test_valid_color_accepted(self, client, session_factory):
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        resp = await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={"key": "branding.primary_color", "value": "#7C3AED", "value_type": "STRING", "category": "BRANDING"},
        )
        assert resp.status_code == 200

    async def test_invalid_key_format(self, client, session_factory):
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        resp = await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={"key": "UPPER-CASE", "value": "x", "value_type": "STRING", "category": "APP"},
        )
        assert resp.status_code == 422

    async def test_invalid_category(self, client, session_factory):
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        resp = await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={"key": "foo.bar", "value": "x", "value_type": "STRING", "category": "NOPE"},
        )
        assert resp.status_code == 422

    async def test_value_type_immutable_on_update(self, client, session_factory):
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={"key": "limits.max_photos", "value": 6, "value_type": "INTEGER", "category": "LIMITS"},
        )
        # PATCH ignores value_type — sending a string value still validates against INTEGER.
        resp = await client.patch(
            "/api/v1/admin/app-config/limits.max_photos",
            headers=auth_headers(admin_tokens),
            json={"value": "six"},
        )
        assert resp.status_code == 422


class TestCache:
    async def test_cache_hit_and_invalidation(self, client, session_factory, monkeypatch):
        import app.services.app_config_service as svc

        fake = _FakeRedis()

        async def _fake_get_redis() -> _FakeRedis:
            return fake

        monkeypatch.setattr(svc, "get_redis", _fake_get_redis)

        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={"key": "branding.app_name", "value": "V1", "value_type": "STRING", "category": "BRANDING"},
        )

        first = await _public(client)
        assert first.status_code == 200
        v1 = first.json()["meta"]["version"]

        # Cache should now hold the payload: mutate DB behind the service's back
        # and confirm the endpoint still serves the cached snapshot.
        async with session_factory() as session:
            from app.db.models import AppConfig

            row = (await session.execute(select(AppConfig).where(AppConfig.key == "branding.app_name"))).scalar_one()
            row.value = "DIRECT_DB_CHANGE"
            await session.commit()

        second = await _public(client)
        assert second.json()["data"]["branding"]["app_name"] == "V1"  # served from cache
        assert second.json()["meta"]["version"] == v1

        # Admin update invalidates the cache; the next read recomputes and re-caches.
        await client.patch(
            "/api/v1/admin/app-config/branding.app_name",
            headers=auth_headers(admin_tokens),
            json={"value": "V2"},
        )
        third = await _public(client)
        assert third.json()["data"]["branding"]["app_name"] == "V2"
        assert third.json()["meta"]["version"] != v1
        # Cache was invalidated and is now repopulated with the new snapshot.
        cached = json.loads(fake._store["app_config:public"])
        assert cached["data"]["branding"]["app_name"] == "V2"

    async def test_redis_unavailable_fails_open(self, client, session_factory):
        # In the test environment REDIS_URL points at a closed port; the endpoint
        # must still serve configuration from PostgreSQL.
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={"key": "branding.app_name", "value": "Resilient", "value_type": "STRING", "category": "BRANDING"},
        )
        resp = await _public(client)
        assert resp.status_code == 200
        assert resp.json()["data"]["branding"]["app_name"] == "Resilient"


class TestAudit:
    async def test_mutations_create_audit_records(self, client, session_factory):
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={"key": "branding.tagline", "value": "Hello", "value_type": "STRING", "category": "BRANDING"},
        )
        await client.patch(
            "/api/v1/admin/app-config/branding.tagline",
            headers=auth_headers(admin_tokens),
            json={"value": "World"},
        )
        await client.delete("/api/v1/admin/app-config/branding.tagline", headers=auth_headers(admin_tokens))

        async with session_factory() as session:
            rows = (
                (await session.execute(select(AuditLog).where(AuditLog.entity_type == "app_config"))).scalars().all()
            )
        actions = [r.action for r in rows]
        assert "app_config.created" in actions
        assert "app_config.updated" in actions
        assert "app_config.deactivated" in actions
        assert all(r.entity_id == "branding.tagline" for r in rows)


class TestSecurity:
    async def test_private_config_never_in_public(self, client, session_factory):
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={
                "key": "app.secret_token",
                "value": "shhh",
                "value_type": "STRING",
                "category": "APP",
                "is_public": False,
            },
        )
        public = (await _public(client)).json()["data"]
        assert "secret_token" not in public["app"]


class TestPricingSafety:
    async def test_payment_amount_comes_from_server(self, client, session_factory):
        admin_tokens = await _promote(client, session_factory, unique_email("admin"), UserRole.ADMIN)
        # Set the authoritative price server-side.
        await client.post(
            "/api/v1/admin/app-config",
            headers=auth_headers(admin_tokens),
            json={
                "key": "pricing.local_job_verification",
                "value": 500,
                "value_type": "INTEGER",
                "category": "PRICING",
                "is_public": True,
            },
        )

        tokens = await register_user(client)
        await create_full_profile(client, tokens, gender="FEMALE")
        # The client cannot send an amount — the endpoint derives it server-side.
        resp = await client.post(
            "/api/v1/verifications/job",
            headers=auth_headers(tokens),
            json={"employment_type": "LOCAL", "employer_name": "Acme"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["amount"] == 500
