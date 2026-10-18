"""Photo upload validation: size limits, magic-byte sniffing, key ownership."""

from app.config.settings import settings
from tests.conftest import auth_headers, register_user

JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"0" * 32


async def _upload_url(client, tokens, filename="pic.jpg", content_type="image/jpeg"):
    return await client.post(
        "/api/v1/profile/photos/upload-url",
        headers=auth_headers(tokens),
        json={"filename": filename, "content_type": content_type},
    )


class TestPhotoValidation:
    async def test_request_upload_url_rejects_unsupported_type(self, client):
        tokens = await register_user(client)
        # Schema-allowed content type, but the extension is not a supported image.
        resp = await _upload_url(client, tokens, filename="doc.tiff", content_type="image/png")
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "UNSUPPORTED_IMAGE_TYPE"

    async def test_request_upload_url_rejects_disallowed_content_type(self, client):
        tokens = await register_user(client)
        resp = await _upload_url(client, tokens, filename="doc.pdf", content_type="application/pdf")
        assert resp.status_code == 422

    async def test_request_upload_url_rejects_mismatched_type(self, client):
        tokens = await register_user(client)
        resp = await _upload_url(client, tokens, filename="pic.png", content_type="image/jpeg")
        assert resp.status_code == 422

    async def test_direct_upload_rejects_non_image_bytes(self, client):
        tokens = await register_user(client)
        resp = await client.post(
            "/api/v1/profile/photos/upload",
            headers=auth_headers(tokens),
            files={"file": ("evil.jpg", b"not an image at all", "image/jpeg")},
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "UNSUPPORTED_IMAGE_TYPE"

    async def test_direct_upload_rejects_empty_file(self, client):
        tokens = await register_user(client)
        resp = await client.post(
            "/api/v1/profile/photos/upload",
            headers=auth_headers(tokens),
            files={"file": ("empty.jpg", b"", "image/jpeg")},
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "PHOTO_EMPTY"

    async def test_direct_upload_rejects_oversized_file(self, client):
        tokens = await register_user(client)
        original = settings.MAX_PHOTO_SIZE_MB
        settings.MAX_PHOTO_SIZE_MB = 0
        try:
            resp = await client.post(
                "/api/v1/profile/photos/upload",
                headers=auth_headers(tokens),
                files={"file": ("big.jpg", JPEG_BYTES, "image/jpeg")},
            )
        finally:
            settings.MAX_PHOTO_SIZE_MB = original
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "PHOTO_TOO_LARGE"

    async def test_direct_upload_accepts_valid_image_and_sniffs_type(self, client):
        tokens = await register_user(client)
        # Client claims a .png/mislabeled type, but the bytes are a JPEG: the
        # server stores the sniffed type, not the client-provided one.
        resp = await client.post(
            "/api/v1/profile/photos/upload",
            headers=auth_headers(tokens),
            files={"file": ("actually.png", JPEG_BYTES, "image/png")},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert "/photos/" in data["url"]
        assert data["url"].endswith(".jpg")

    async def test_confirm_rejects_other_users_key(self, client):
        tokens_a = await register_user(client)
        tokens_b = await register_user(client)
        req = await _upload_url(client, tokens_a)
        object_key = req.json()["data"]["object_key"]

        from app.services.storage import build_storage

        await build_storage().put_object(object_key, JPEG_BYTES)

        resp = await client.post(
            "/api/v1/profile/photos/confirm",
            headers=auth_headers(tokens_b),
            json={"object_key": object_key, "content_type": "image/jpeg"},
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "INVALID_OBJECT_KEY"

    async def test_confirm_rejects_missing_object(self, client):
        tokens = await register_user(client)
        req = await _upload_url(client, tokens)
        object_key = req.json()["data"]["object_key"]

        resp = await client.post(
            "/api/v1/profile/photos/confirm",
            headers=auth_headers(tokens),
            json={"object_key": object_key, "content_type": "image/jpeg"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "PHOTO_OBJECT_NOT_FOUND"
