import pyotp

from tests.conftest import auth_headers, register_user, unique_email


class TestTotpSetup:
    async def test_setup_returns_secret_and_recovery_codes(self, client):
        tokens = await register_user(client)
        resp = await client.post("/api/v1/auth/totp/setup", headers=auth_headers(tokens))
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["secret"]
        assert data["otpauth_url"].startswith("otpauth://")
        assert len(data["recovery_codes"]) == 8

    async def test_status_default_disabled(self, client):
        tokens = await register_user(client)
        resp = await client.get("/api/v1/auth/totp/status", headers=auth_headers(tokens))
        assert resp.json()["data"]["enabled"] is False


class TestTotpEnable:
    async def _setup(self, client) -> tuple[dict, str]:
        tokens = await register_user(client)
        resp = await client.post("/api/v1/auth/totp/setup", headers=auth_headers(tokens))
        secret = resp.json()["data"]["secret"]
        return tokens, secret

    async def test_enable_requires_valid_code(self, client):
        tokens, secret = await self._setup(client)
        totp = pyotp.TOTP(secret)
        resp = await client.post("/api/v1/auth/totp/enable", headers=auth_headers(tokens), json={"code": totp.now()})
        assert resp.status_code == 200
        status = await client.get("/api/v1/auth/totp/status", headers=auth_headers(tokens))
        assert status.json()["data"]["enabled"] is True

    async def test_enable_rejects_bad_code(self, client):
        tokens, secret = await self._setup(client)
        resp = await client.post("/api/v1/auth/totp/enable", headers=auth_headers(tokens), json={"code": "000000"})
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_TOTP"

    async def test_disable_requires_password(self, client):
        tokens, secret = await self._setup(client)
        totp = pyotp.TOTP(secret)
        await client.post("/api/v1/auth/totp/enable", headers=auth_headers(tokens), json={"code": totp.now()})
        resp = await client.post(
            "/api/v1/auth/totp/disable", headers=auth_headers(tokens), json={"password": "Wrongpass1"}
        )
        assert resp.status_code == 401
        resp = await client.post(
            "/api/v1/auth/totp/disable", headers=auth_headers(tokens), json={"password": "Testpass123"}
        )
        assert resp.status_code == 200
        status = await client.get("/api/v1/auth/totp/status", headers=auth_headers(tokens))
        assert status.json()["data"]["enabled"] is False


class TestTotpLogin:
    async def test_login_without_totp_still_returns_tokens(self, client):
        email = unique_email()
        tokens = await register_user(client, email=email)
        resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Testpass123"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()["data"]

    async def test_login_requires_mfa_when_enabled(self, client):
        email = unique_email()
        tokens = await register_user(client, email=email)
        resp = await client.post("/api/v1/auth/totp/setup", headers=auth_headers(tokens))
        secret = resp.json()["data"]["secret"]
        totp = pyotp.TOTP(secret)
        await client.post("/api/v1/auth/totp/enable", headers=auth_headers(tokens), json={"code": totp.now()})

        resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Testpass123"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["requires_2fa"] is True
        assert data["mfa_token"]
        assert "access_token" not in data

        # Completing with a TOTP code issues a real token pair.
        resp2 = await client.post(
            "/api/v1/auth/totp/verify",
            json={"mfa_token": data["mfa_token"], "code": totp.now()},
        )
        assert resp2.status_code == 200
        assert "access_token" in resp2.json()["data"]

    async def test_mfa_rejects_bad_code(self, client):
        email = unique_email()
        tokens = await register_user(client, email=email)
        resp = await client.post("/api/v1/auth/totp/setup", headers=auth_headers(tokens))
        secret = resp.json()["data"]["secret"]
        totp = pyotp.TOTP(secret)
        await client.post("/api/v1/auth/totp/enable", headers=auth_headers(tokens), json={"code": totp.now()})

        resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Testpass123"})
        resp2 = await client.post(
            "/api/v1/auth/totp/verify",
            json={"mfa_token": resp.json()["data"]["mfa_token"], "code": "000000"},
        )
        assert resp2.status_code == 401
        assert resp2.json()["error"]["code"] == "INVALID_TOTP"

    async def test_recovery_code_login(self, client):
        email = unique_email()
        tokens = await register_user(client, email=email)
        resp = await client.post("/api/v1/auth/totp/setup", headers=auth_headers(tokens))
        data = resp.json()["data"]
        recovery_code = data["recovery_codes"][0]
        totp = pyotp.TOTP(data["secret"])
        await client.post("/api/v1/auth/totp/enable", headers=auth_headers(tokens), json={"code": totp.now()})

        resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Testpass123"})
        resp2 = await client.post(
            "/api/v1/auth/totp/verify",
            json={"mfa_token": resp.json()["data"]["mfa_token"], "code": recovery_code},
        )
        assert resp2.status_code == 200
        assert "access_token" in resp2.json()["data"]

        # Recovery codes are single-use.
        resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Testpass123"})
        resp3 = await client.post(
            "/api/v1/auth/totp/verify",
            json={"mfa_token": resp.json()["data"]["mfa_token"], "code": recovery_code},
        )
        assert resp3.status_code == 401
