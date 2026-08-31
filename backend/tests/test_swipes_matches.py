from tests.conftest import auth_headers, create_full_profile, register_user


class TestSwipes:
    async def test_like(self, client):
        tokens_a = await register_user(client)
        tokens_b = await register_user(client)
        a = await create_full_profile(client, tokens_a, gender="MALE")
        b = await create_full_profile(client, tokens_b, gender="FEMALE")

        resp = await client.post(
            "/api/v1/swipes",
            headers=auth_headers(tokens_a),
            json={"target_user_id": b["user_id"], "action": "LIKE"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["match_created"] is False

    async def test_pass(self, client):
        tokens_a = await register_user(client)
        tokens_b = await register_user(client)
        a = await create_full_profile(client, tokens_a, gender="MALE")
        b = await create_full_profile(client, tokens_b, gender="FEMALE")

        resp = await client.post(
            "/api/v1/swipes",
            headers=auth_headers(tokens_a),
            json={"target_user_id": b["user_id"], "action": "PASS"},
        )
        assert resp.status_code == 200

    async def test_self_swipe_forbidden(self, client):
        tokens = await register_user(client)
        me = await create_full_profile(client, tokens, gender="FEMALE")
        resp = await client.post(
            "/api/v1/swipes",
            headers=auth_headers(tokens),
            json={"target_user_id": me["user_id"], "action": "LIKE"},
        )
        assert resp.status_code == 403

    async def test_duplicate_like_conflict(self, client):
        tokens_a = await register_user(client)
        tokens_b = await register_user(client)
        await create_full_profile(client, tokens_a, gender="MALE")
        b = await create_full_profile(client, tokens_b, gender="FEMALE")

        await client.post(
            "/api/v1/swipes",
            headers=auth_headers(tokens_a),
            json={"target_user_id": b["user_id"], "action": "LIKE"},
        )
        resp = await client.post(
            "/api/v1/swipes",
            headers=auth_headers(tokens_a),
            json={"target_user_id": b["user_id"], "action": "LIKE"},
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "DUPLICATE_SWIPE"

    async def test_mutual_like_creates_match(self, client):
        tokens_a = await register_user(client)
        tokens_b = await register_user(client)
        a = await create_full_profile(client, tokens_a, gender="MALE")
        b = await create_full_profile(client, tokens_b, gender="FEMALE")

        r1 = await client.post(
            "/api/v1/swipes",
            headers=auth_headers(tokens_a),
            json={"target_user_id": b["user_id"], "action": "LIKE"},
        )
        r2 = await client.post(
            "/api/v1/swipes",
            headers=auth_headers(tokens_b),
            json={"target_user_id": a["user_id"], "action": "LIKE"},
        )
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r2.json()["data"]["match_created"] is True
        assert r2.json()["data"]["match_id"] is not None

    async def test_swipe_self_deleted_user_blocked(self, client):
        tokens_a = await register_user(client)
        tokens_b = await register_user(client)
        await create_full_profile(client, tokens_a, gender="MALE")
        b = await create_full_profile(client, tokens_b, gender="FEMALE")

        # Block then attempt swipe.
        await client.post(
            f"/api/v1/blocks/{b['user_id']}",
            headers=auth_headers(tokens_a),
        )
        resp = await client.post(
            "/api/v1/swipes",
            headers=auth_headers(tokens_a),
            json={"target_user_id": b["user_id"], "action": "LIKE"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "BLOCKED"


class TestMatches:
    async def _make_match(self, client):
        tokens_a = await register_user(client)
        tokens_b = await register_user(client)
        a = await create_full_profile(client, tokens_a, gender="MALE")
        b = await create_full_profile(client, tokens_b, gender="FEMALE")
        await client.post(
            "/api/v1/swipes",
            headers=auth_headers(tokens_a),
            json={"target_user_id": b["user_id"], "action": "LIKE"},
        )
        r2 = await client.post(
            "/api/v1/swipes",
            headers=auth_headers(tokens_b),
            json={"target_user_id": a["user_id"], "action": "LIKE"},
        )
        return tokens_a, tokens_b, a, b, r2.json()["data"]["match_id"]

    async def test_list_matches(self, client):
        tokens_a, tokens_b, a, b, match_id = await self._make_match(client)
        resp = await client.get("/api/v1/matches", headers=auth_headers(tokens_a))
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1
        assert resp.json()["data"][0]["user_id"] == b["user_id"]

    async def test_unmatch(self, client):
        tokens_a, tokens_b, a, b, match_id = await self._make_match(client)
        resp = await client.delete(f"/api/v1/matches/{match_id}", headers=auth_headers(tokens_a))
        assert resp.status_code == 200
        resp2 = await client.get("/api/v1/matches", headers=auth_headers(tokens_a))
        assert resp2.json()["data"] == []

    async def test_cannot_unmatch_others_match(self, client):
        tokens_a, tokens_b, a, b, match_id = await self._make_match(client)
        tokens_c = await register_user(client)
        await create_full_profile(client, tokens_c, gender="MALE")
        resp = await client.delete(f"/api/v1/matches/{match_id}", headers=auth_headers(tokens_c))
        assert resp.status_code == 403 or resp.status_code == 404
