from tests.conftest import auth_headers, create_full_profile, register_user


class TestRecommendations:
    async def test_feed_excludes_self_and_swiped(self, client):
        tokens_a = await register_user(client)
        tokens_b = await register_user(client)
        a = await create_full_profile(client, tokens_a, gender="MALE")
        b = await create_full_profile(client, tokens_b, gender="FEMALE")

        feed = await client.get("/api/v1/recommendations", headers=auth_headers(tokens_a))
        assert feed.status_code == 200
        items = feed.json()["data"]["items"]
        assert items, "expected at least one candidate"
        ids = [r["candidate_user_id"] for r in items]
        assert a["user_id"] not in ids
        assert b["user_id"] in ids

    async def test_scored_items_have_reason_codes(self, client):
        tokens_a = await register_user(client)
        tokens_b = await register_user(client)
        await create_full_profile(
            client,
            tokens_a,
            gender="MALE",
        )
        await create_full_profile(client, tokens_b, gender="FEMALE")

        feed = await client.get("/api/v1/recommendations", headers=auth_headers(tokens_a))
        item = feed.json()["data"]["items"][0]
        assert 0 <= item["score"] <= 100
        assert isinstance(item["reason_codes"], list)

    async def test_feed_excludes_blocked(self, client):
        tokens_a = await register_user(client)
        tokens_b = await register_user(client)
        a = await create_full_profile(client, tokens_a, gender="MALE")
        b = await create_full_profile(client, tokens_b, gender="FEMALE")

        await client.post(f"/api/v1/blocks/{b['user_id']}", headers=auth_headers(tokens_a))
        feed = await client.get("/api/v1/recommendations", headers=auth_headers(tokens_a))
        ids = [r["candidate_user_id"] for r in feed.json()["data"]["items"]]
        assert b["user_id"] not in ids

    async def test_excludes_already_matched(self, client):
        tokens_a = await register_user(client)
        tokens_b = await register_user(client)
        a = await create_full_profile(client, tokens_a, gender="MALE")
        b = await create_full_profile(client, tokens_b, gender="FEMALE")

        await client.post(
            "/api/v1/swipes",
            headers=auth_headers(tokens_a),
            json={"target_user_id": b["user_id"], "action": "LIKE"},
        )
        await client.post(
            "/api/v1/swipes",
            headers=auth_headers(tokens_b),
            json={"target_user_id": a["user_id"], "action": "LIKE"},
        )

        feed = await client.get("/api/v1/recommendations", headers=auth_headers(tokens_a))
        ids = [r["candidate_user_id"] for r in feed.json()["data"]["items"]]
        assert b["user_id"] not in ids
