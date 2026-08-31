from datetime import UTC

from tests.conftest import auth_headers, login_user, register_user, unique_email


class TestRegistration:
    async def test_register_returns_tokens(self, client):
        data = await register_user(client)
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_register_duplicate_email_fails(self, client):
        email = unique_email()
        await register_user(client, email=email)
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Testpass123"},
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "ACCOUNT_EXISTS"

    async def test_register_weak_password_fails(self, client):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": unique_email(), "password": "short"},
        )
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success(self, client):
        email = unique_email()
        await register_user(client, email=email)
        data = await login_user(client, email)
        assert data["access_token"]

    async def test_login_invalid_password(self, client):
        email = unique_email()
        await register_user(client, email=email)
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Wrongpass1"},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"

    async def test_login_unknown_user(self, client):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "Testpass123"},
        )
        assert resp.status_code == 401


class TestRefresh:
    async def test_refresh_rotates_token(self, client):
        tokens = await register_user(client)
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp.status_code == 200
        new_tokens = resp.json()["data"]
        assert new_tokens["refresh_token"] != tokens["refresh_token"]

        # Old refresh token must now be revoked.
        resp2 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp2.status_code == 401

    async def test_refresh_invalid_token(self, client):
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "not-a-jwt"},
        )
        assert resp.status_code == 401


class TestAuthz:
    async def test_me_requires_auth(self, client):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_me_returns_account(self, client):
        email = unique_email()
        tokens = await register_user(client, email=email)
        resp = await client.get("/api/v1/auth/me", headers=auth_headers(tokens))
        assert resp.status_code == 200
        assert resp.json()["data"]["email"] == email

    async def test_invalid_access_token(self, client):
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer garbage.token.here"},
        )
        assert resp.status_code == 401

    async def test_expired_access_token(self, client):
        from datetime import datetime, timedelta

        import jwt

        from app.config.settings import settings

        email = unique_email()
        tokens = await register_user(client, email=email)

        # Build an already-expired access token for the same user id.
        import uuid

        sub = None
        decoded = jwt.decode(tokens["access_token"], settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        sub = decoded["sub"]
        expired = jwt.encode(
            {
                "sub": sub,
                "type": "access",
                "iat": datetime.now(UTC) - timedelta(hours=2),
                "exp": datetime.now(UTC) - timedelta(hours=1),
                "jti": str(uuid.uuid4()),
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
        assert resp.status_code == 401


class TestLogout:
    async def test_logout_revokes_refresh(self, client):
        tokens = await register_user(client)
        resp = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp.status_code == 200
        resp2 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp2.status_code == 401
