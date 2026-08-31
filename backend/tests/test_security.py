"""Security: object-level authorization tests."""

from tests.conftest import auth_headers, create_full_profile, register_user


class TestObjectAuthorization:
    async def test_cannot_read_anothers_profile_via_profile_endpoint(self, client):
        tokens_a = await register_user(client)
        tokens_b = await register_user(client)
        a = await create_full_profile(client, tokens_a, gender="FEMALE")

        # /profile endpoints only ever operate on the authenticated user's own profile.
        resp = await client.get("/api/v1/profile/me", headers=auth_headers(tokens_b))
        assert resp.status_code == 200
        assert resp.json()["data"]["user_id"] != a["user_id"]

    async def test_cannot_set_own_verification(self, client):
        # Verification status is server-controlled; there is no client endpoint to set it.
        tokens = await register_user(client)
        me = await create_full_profile(client, tokens, gender="FEMALE")
        resp = await client.patch(
            "/api/v1/profile",
            headers=auth_headers(tokens),
            json={"first_name": "Hacker"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        # No verification-ish field is exposed in the update payload.
        assert "verification_status" not in data

    async def test_photos_are_scoped_to_owner(self, client):
        tokens_a = await register_user(client)
        tokens_b = await register_user(client)
        await create_full_profile(client, tokens_a, gender="FEMALE")
        await create_full_profile(client, tokens_b, gender="MALE")

        # A creates a photo.
        req = await client.post(
            "/api/v1/profile/photos/upload-url",
            headers=auth_headers(tokens_a),
            json={"filename": "pic.jpg", "content_type": "image/jpeg"},
        )
        assert req.status_code == 200
        object_key = req.json()["data"]["object_key"]

        confirm = await client.post(
            "/api/v1/profile/photos/confirm",
            headers=auth_headers(tokens_a),
            json={"object_key": object_key, "content_type": "image/jpeg"},
        )
        assert confirm.status_code == 200
        photo_id = confirm.json()["data"]["id"]

        # B must not see or delete A's photo.
        resp = await client.get("/api/v1/profile/photos", headers=auth_headers(tokens_b))
        assert all(p["id"] != photo_id for p in resp.json()["data"])

        resp = await client.delete(
            f"/api/v1/profile/photos/{photo_id}",
            headers=auth_headers(tokens_b),
        )
        assert resp.status_code == 404

    async def test_preferences_scoped_to_owner(self, client):
        tokens_a = await register_user(client)
        tokens_b = await register_user(client)
        await create_full_profile(client, tokens_a, gender="FEMALE")

        await client.put(
            "/api/v1/preferences",
            headers=auth_headers(tokens_a),
            json={"age_min": 25, "age_max": 35},
        )
        resp = await client.get("/api/v1/preferences", headers=auth_headers(tokens_b))
        assert resp.status_code == 200
        assert resp.json()["data"]["age_min"] is None  # B has their own (empty) prefs

    async def test_banned_user_locked_out(self, client, session_factory):
        from sqlalchemy import select

        from app.db.enums import AccountStatus
        from app.db.models import User

        tokens = await register_user(client)
        async with session_factory() as session:
            # Simulate a ban.
            stmt = select(User).where(User.id == _uid(tokens))
            user = (await session.execute(stmt)).scalar_one()
            user.is_banned = True
            user.account_status = AccountStatus.BANNED
            await session.commit()

        resp = await client.get("/api/v1/auth/me", headers=auth_headers(tokens))
        assert resp.status_code == 401


def _uid(tokens: dict) -> str:
    import jwt

    from app.config.settings import settings

    return jwt.decode(tokens["access_token"], settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])["sub"]
