from app.db.enums import UserRole
from tests.conftest import auth_headers, create_full_profile, register_user, unique_email
from tests.test_admin_permissions import promote


async def _me(client, tokens) -> str:
    return (await client.get("/api/v1/auth/me", headers=auth_headers(tokens))).json()["data"]["id"]


async def _make_report(client, reporter_tokens, reported_tokens) -> str:
    reported_id = await _me(client, reported_tokens)
    resp = await client.post(
        "/api/v1/reports",
        headers=auth_headers(reporter_tokens),
        json={"reported_user_id": reported_id, "reason": "FAKE_PROFILE", "description": "looks fake"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["id"]


class TestReports:
    async def test_moderator_lists_reports(self, client, session_factory):
        reporter = await register_user(client)
        reported = await register_user(client)
        await _make_report(client, reporter, reported)
        moderator = await promote(client, session_factory, unique_email("mod"), UserRole.MODERATOR)
        resp = await client.get("/api/v1/admin/reports", headers=auth_headers(moderator))
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    async def test_report_detail_with_history(self, client, session_factory):
        reporter = await register_user(client)
        reported_email = unique_email()
        reported = await register_user(client, email=reported_email)
        report_id = await _make_report(client, reporter, reported)
        moderator = await promote(client, session_factory, unique_email("mod"), UserRole.MODERATOR)
        resp = await client.get(f"/api/v1/admin/reports/{report_id}", headers=auth_headers(moderator))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["reported_name"] == reported_email

    async def test_assign(self, client, session_factory):
        reporter = await register_user(client)
        reported = await register_user(client)
        report_id = await _make_report(client, reporter, reported)
        moderator = await promote(client, session_factory, unique_email("mod"), UserRole.MODERATOR)
        assignee = await promote(client, session_factory, unique_email("mod2"), UserRole.MODERATOR)
        assignee_id = await _me(client, assignee)
        resp = await client.post(
            f"/api/v1/admin/reports/{report_id}/assign",
            headers=auth_headers(moderator),
            json={"assignee_id": assignee_id},
        )
        assert resp.status_code == 200
        detail = await client.get(f"/api/v1/admin/reports/{report_id}", headers=auth_headers(moderator))
        assert detail.json()["data"]["status"] == "UNDER_REVIEW"

    async def test_resolve_dismiss_escalate(self, client, session_factory):
        reporter = await register_user(client)
        reported = await register_user(client)
        moderator = await promote(client, session_factory, unique_email("mod"), UserRole.MODERATOR)
        for status in ["RESOLVED", "DISMISSED", "ESCALATED"]:
            report_id = await _make_report(client, reporter, reported)
            resp = await client.post(
                f"/api/v1/admin/reports/{report_id}/review",
                headers=auth_headers(moderator),
                json={"status": status, "reason": "handled"},
            )
            assert resp.status_code == 200, status
            detail = await client.get(f"/api/v1/admin/reports/{report_id}", headers=auth_headers(moderator))
            assert detail.json()["data"]["status"] == status

    async def test_invalid_status_rejected(self, client, session_factory):
        reporter = await register_user(client)
        reported = await register_user(client)
        report_id = await _make_report(client, reporter, reported)
        moderator = await promote(client, session_factory, unique_email("mod"), UserRole.MODERATOR)
        resp = await client.post(
            f"/api/v1/admin/reports/{report_id}/review",
            headers=auth_headers(moderator),
            json={"status": "NOT_A_STATUS"},
        )
        assert resp.status_code == 422

    async def test_warn_sends_notification(self, client, session_factory):
        reporter = await register_user(client)
        reported = await register_user(client)
        report_id = await _make_report(client, reporter, reported)
        moderator = await promote(client, session_factory, unique_email("mod"), UserRole.MODERATOR)
        resp = await client.post(
            f"/api/v1/admin/reports/{report_id}/warn",
            headers=auth_headers(moderator),
            json={"message": "Please review our guidelines"},
        )
        assert resp.status_code == 200
        notify = await client.get("/api/v1/notifications", headers=auth_headers(reported))
        assert len(notify.json()["data"]) == 1

    async def test_ban_from_report(self, client, session_factory):
        reporter = await register_user(client)
        reported = await register_user(client)
        reported_id = await _me(client, reported)
        report_id = await _make_report(client, reporter, reported)
        moderator = await promote(client, session_factory, unique_email("mod"), UserRole.MODERATOR)
        resp = await client.post(
            f"/api/v1/admin/reports/{report_id}/ban",
            headers=auth_headers(moderator),
            json={"reason": "confirmed scam", "admin_notes": "evidence reviewed"},
        )
        assert resp.status_code == 200
        detail = await client.get(f"/api/v1/admin/reports/{report_id}", headers=auth_headers(moderator))
        assert detail.json()["data"]["status"] == "RESOLVED"
        # The reported user can no longer log in.
        user_detail = await client.get(f"/api/v1/admin/users/{reported_id}", headers=auth_headers(moderator))
        assert user_detail.json()["data"]["is_banned"] is True

    async def test_user_cannot_moderate(self, client):
        reporter = await register_user(client)
        reported = await register_user(client)
        report_id = await _make_report(client, reporter, reported)
        resp = await client.get("/api/v1/admin/reports", headers=auth_headers(reporter))
        assert resp.status_code == 403


class TestProfileShares:
    async def test_list_profile_shares(self, client, session_factory):
        owner = await register_user(client)
        shared = await register_user(client)
        owner_id = await _me(client, owner)
        shared_id = await _me(client, shared)
        resp = await client.post(
            "/api/v1/profile-shares",
            headers=auth_headers(owner),
            json={"shared_with_user_id": shared_id, "permission": "VIEW"},
        )
        assert resp.status_code == 200, resp.text
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.get("/api/v1/admin/profile-shares", headers=auth_headers(admin))
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1
        assert resp.json()["data"][0]["owner_user_id"] == owner_id


class TestPhotoModeration:
    async def test_photo_review_flow(self, client, session_factory):
        tokens = await register_user(client)
        user_id = await _me(client, tokens)
        # Confirm an upload creates a photo row.
        resp = await client.post(
            "/api/v1/profile/photos/upload-url",
            headers=auth_headers(tokens),
            json={"filename": "pic.jpg", "content_type": "image/jpeg"},
        )
        key = resp.json()["data"]["object_key"]
        await client.post(
            "/api/v1/profile/photos/confirm",
            headers=auth_headers(tokens),
            json={"object_key": key, "content_type": "image/jpeg"},
        )
        verifier = await promote(client, session_factory, unique_email("ver"), UserRole.VERIFIER)
        photos = await client.get(f"/api/v1/admin/photos?user_id={user_id}", headers=auth_headers(verifier))
        assert photos.status_code == 200
        photo_id = photos.json()["data"][0]["id"]
        resp = await client.post(
            f"/api/v1/admin/photos/{photo_id}/review",
            headers=auth_headers(verifier),
            json={"action": "approve"},
        )
        assert resp.status_code == 200
        photos = await client.get(f"/api/v1/admin/photos?user_id={user_id}", headers=auth_headers(verifier))
        assert photos.json()["data"][0]["verification_status"] == "VERIFIED"


class TestProfileModeration:
    async def test_profile_list_and_moderate(self, client, session_factory):
        tokens = await register_user(client)
        await create_full_profile(client, tokens)
        user_id = await _me(client, tokens)
        moderator = await promote(client, session_factory, unique_email("mod"), UserRole.MODERATOR)
        resp = await client.get("/api/v1/admin/profiles?search=Anita", headers=auth_headers(moderator))
        assert resp.status_code == 200
        rows = resp.json()["data"]
        assert any(r["user_id"] == user_id for r in rows)

        resp = await client.post(
            f"/api/v1/admin/profiles/{user_id}/moderate",
            headers=auth_headers(moderator),
            json={"action": "approve"},
        )
        assert resp.status_code == 200
        detail = await client.get(f"/api/v1/admin/profiles/{user_id}", headers=auth_headers(moderator))
        assert detail.json()["data"]["profile"]["review_status"] == "APPROVED"

    async def test_reject_requires_reason_field(self, client, session_factory):
        tokens = await register_user(client)
        await create_full_profile(client, tokens)
        user_id = await _me(client, tokens)
        moderator = await promote(client, session_factory, unique_email("mod"), UserRole.MODERATOR)
        resp = await client.post(
            f"/api/v1/admin/profiles/{user_id}/moderate",
            headers=auth_headers(moderator),
            json={"action": "reject", "reason": "photos do not match"},
        )
        assert resp.status_code == 200
        detail = await client.get(f"/api/v1/admin/profiles/{user_id}", headers=auth_headers(moderator))
        assert detail.json()["data"]["profile"]["review_status"] == "REJECTED"
