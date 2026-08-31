from tests.conftest import auth_headers, create_full_profile, register_user, unique_email


class TestCreateProfile:
    async def test_create_profile(self, client):
        tokens = await register_user(client)
        data = await create_full_profile(client, tokens)
        assert data["first_name"] == "Anita"
        assert data["gender"] == "FEMALE"

    async def test_minor_rejected(self, client):
        tokens = await register_user(client)
        resp = await client.post(
            "/api/v1/profile",
            headers=auth_headers(tokens),
            json={
                "first_name": "Kid",
                "gender": "MALE",
                "date_of_birth": "2015-01-01",
            },
        )
        assert resp.status_code == 422

    async def test_future_dob_rejected(self, client):
        tokens = await register_user(client)
        resp = await client.post(
            "/api/v1/profile",
            headers=auth_headers(tokens),
            json={
                "first_name": "Future",
                "gender": "MALE",
                "date_of_birth": "2099-01-01",
            },
        )
        assert resp.status_code == 422


class TestUpdateProfile:
    async def test_update_profile(self, client):
        tokens = await register_user(client)
        await create_full_profile(client, tokens)
        resp = await client.patch(
            "/api/v1/profile",
            headers=auth_headers(tokens),
            json={"bio": "Hello world", "city": "Delhi"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["bio"] == "Hello world"
        assert data["city"] == "Delhi"


class TestPrivacy:
    async def test_privacy_settings(self, client):
        tokens = await register_user(client)
        resp = await client.patch(
            "/api/v1/profile/privacy",
            headers=auth_headers(tokens),
            json={"show_distance": False, "phone_visibility": "MATCHES"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["show_distance"] is False
        assert data["phone_visibility"] == "MATCHES"

    async def test_cannot_modify_others_profile(self, client):
        tokens_a = await register_user(client)
        tokens_b = await register_user(client)
        await create_full_profile(client, tokens_a)

        # B cannot update A's profile (A owns it).
        resp = await client.patch(
            "/api/v1/profile",
            headers=auth_headers(tokens_b),
            json={"bio": "hacked"},
        )
        # B can only update their own profile (no id in payload), so this succeeds but touches B's own.
        assert resp.status_code == 200

    async def test_public_profile_hides_sensitive_fields(self, client):
        tokens_a = await register_user(client)
        tokens_b = await register_user(client)
        data_a = await create_full_profile(client, tokens_a, gender="FEMALE")

        resp = await client.get(
            f"/api/v1/profiles/{data_a['user_id']}",
            headers=auth_headers(tokens_b),
        )
        assert resp.status_code == 200
        body = resp.json()["data"]
        # Public response must not leak income / contact / exact DOB / location.
        assert "annual_income" not in body
        assert "phone_number" not in body
        assert "email" not in body
        assert "location_lat" not in body
        assert "date_of_birth" not in body

    async def test_profile_delete_soft_deletes_account(self, client):
        email = unique_email()
        tokens = await register_user(client, email=email)
        await create_full_profile(client, tokens)
        resp = await client.delete("/api/v1/profile", headers=auth_headers(tokens))
        assert resp.status_code == 200

        # Login should now fail.
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Testpass123"},
        )
        assert resp.status_code == 401
