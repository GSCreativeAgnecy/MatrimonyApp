from tests.conftest import auth_headers, create_full_profile, register_user


async def _make_match(client):
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
    return tokens_a, tokens_b, a, b


class TestConversations:
    async def test_start_conversation_with_match(self, client):
        tokens_a, tokens_b, a, b = await _make_match(client)
        resp = await client.post(
            "/api/v1/conversations",
            headers=auth_headers(tokens_a),
            json={"user_id": b["user_id"]},
        )
        assert resp.status_code == 200
        conv_id = resp.json()["data"]["id"]
        assert conv_id

    async def test_start_conversation_without_match_forbidden(self, client):
        tokens_a = await register_user(client)
        tokens_b = await register_user(client)
        a = await create_full_profile(client, tokens_a, gender="MALE")
        b = await create_full_profile(client, tokens_b, gender="FEMALE")
        resp = await client.post(
            "/api/v1/conversations",
            headers=auth_headers(tokens_a),
            json={"user_id": b["user_id"]},
        )
        assert resp.status_code == 403

    async def test_list_conversations(self, client):
        tokens_a, tokens_b, a, b = await _make_match(client)
        await client.post(
            "/api/v1/conversations",
            headers=auth_headers(tokens_a),
            json={"user_id": b["user_id"]},
        )
        resp = await client.get("/api/v1/conversations", headers=auth_headers(tokens_a))
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1


class TestMessages:
    async def test_send_and_list_message(self, client):
        tokens_a, tokens_b, a, b = await _make_match(client)
        conv_resp = await client.post(
            "/api/v1/conversations",
            headers=auth_headers(tokens_a),
            json={"user_id": b["user_id"]},
        )
        conv_id = conv_resp.json()["data"]["id"]

        resp = await client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            headers=auth_headers(tokens_a),
            json={"message_type": "TEXT", "body": "Hi there!"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["body"] == "Hi there!"

        lst = await client.get(
            f"/api/v1/conversations/{conv_id}/messages",
            headers=auth_headers(tokens_a),
        )
        assert lst.status_code == 200
        assert len(lst.json()["data"]) == 1

    async def test_mark_read(self, client):
        tokens_a, tokens_b, a, b = await _make_match(client)
        conv_resp = await client.post(
            "/api/v1/conversations",
            headers=auth_headers(tokens_a),
            json={"user_id": b["user_id"]},
        )
        conv_id = conv_resp.json()["data"]["id"]
        await client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            headers=auth_headers(tokens_a),
            json={"body": "hello"},
        )
        resp = await client.post(
            f"/api/v1/conversations/{conv_id}/read",
            headers=auth_headers(tokens_b),
        )
        assert resp.status_code == 200

    async def test_non_participant_cannot_read_messages(self, client):
        tokens_a, tokens_b, a, b = await _make_match(client)
        conv_resp = await client.post(
            "/api/v1/conversations",
            headers=auth_headers(tokens_a),
            json={"user_id": b["user_id"]},
        )
        conv_id = conv_resp.json()["data"]["id"]

        tokens_c = await register_user(client)
        await create_full_profile(client, tokens_c, gender="MALE")
        resp = await client.get(
            f"/api/v1/conversations/{conv_id}/messages",
            headers=auth_headers(tokens_c),
        )
        assert resp.status_code == 404
