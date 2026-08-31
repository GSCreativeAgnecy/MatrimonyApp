"""Object storage abstraction.

Supports S3-compatible storage and a local filesystem backend for development.
Routers depend on the `StorageBackend` protocol, never on boto3 specifics.
"""

import asyncio
import os
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from app.config.settings import settings


class StorageError(Exception):
    pass


class StorageBackend(Protocol):
    async def put_object(self, key: str, data: bytes, *, content_type: str | None = None) -> str: ...

    async def delete_object(self, key: str) -> None: ...

    async def object_exists(self, key: str) -> bool: ...

    async def presigned_upload_url(self, key: str, *, content_type: str | None = None) -> str: ...

    async def presigned_download_url(self, key: str) -> str: ...


class LocalStorage:
    """Filesystem backend for development. URLs are served by the API itself."""

    def __init__(self, base_path: str | None = None) -> None:
        self.base_path = Path(base_path or settings.LOCAL_STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        safe = key.replace("..", "").lstrip("/")
        path = (self.base_path / safe).resolve()
        if not path.is_relative_to(self.base_path.resolve()):
            raise StorageError("Invalid key")
        return path

    async def put_object(self, key: str, data: bytes, *, content_type: str | None = None) -> str:
        def _write() -> None:
            path = self._path_for(key)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        await asyncio.to_thread(_write)
        return f"/static/{key}"

    async def delete_object(self, key: str) -> None:
        path = self._path_for(key)
        if path.exists():
            path.unlink()

    async def object_exists(self, key: str) -> bool:
        return self._path_for(key).exists()

    async def presigned_upload_url(self, key: str, *, content_type: str | None = None) -> str:
        return f"/static/{key}"

    async def presigned_download_url(self, key: str) -> str:
        return f"/static/{key}"


class S3Storage:
    def __init__(self) -> None:
        import boto3  # imported lazily to keep app importable without AWS creds

        self._client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
        )
        self.bucket = settings.S3_BUCKET

    async def put_object(self, key: str, data: bytes, *, content_type: str | None = None) -> str:
        def _put() -> None:
            self._client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)

        await asyncio.to_thread(_put)
        return key

    async def delete_object(self, key: str) -> None:
        def _delete() -> None:
            self._client.delete_object(Bucket=self.bucket, Key=key)

        await asyncio.to_thread(_delete)

    async def object_exists(self, key: str) -> bool:
        def _head() -> bool:
            try:
                self._client.head_object(Bucket=self.bucket, Key=key)
                return True
            except Exception:
                return False

        return await asyncio.to_thread(_head)

    async def presigned_upload_url(self, key: str, *, content_type: str | None = None) -> str:
        def _url() -> str:
            params = {
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": content_type,
            }
            return self._client.generate_presigned_url(
                "put_object", Params=params, ExpiresIn=settings.S3_UPLOAD_URL_EXPIRES
            )

        return await asyncio.to_thread(_url)

    async def presigned_download_url(self, key: str) -> str:
        def _url() -> str:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=settings.S3_DOWNLOAD_URL_EXPIRES,
            )

        return await asyncio.to_thread(_url)


def build_storage() -> StorageBackend:
    if settings.STORAGE_BACKEND == "s3":
        return S3Storage()
    return LocalStorage()


def new_object_key(user_id: str, original_name: str, ext: str) -> str:
    safe_ext = (ext or ".jpg").lstrip(".").lower()[:10]
    return f"photos/{user_id}/{uuid4().hex}.{safe_ext}"


def extract_extension(filename: str) -> str:
    return os.path.splitext(filename)[1]
