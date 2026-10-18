import builtins
import os
from datetime import UTC
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import NotFoundError, ValidationAppError
from app.config.settings import settings
from app.db.enums import PhotoVerificationStatus
from app.db.models import Photo, User
from app.repositories.base import BaseRepository
from app.services.audit_service import AuditService
from app.services.storage import StorageBackend, new_object_key

# Server-side image allowlist. Client-provided MIME types/filenames are never
# trusted; the stored type is derived from the file's magic bytes.
_EXT_TO_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".heic": "image/heic",
    ".heif": "image/heif",
}


def _sniff_image(data: bytes) -> tuple[str, str] | None:
    """Return (mime, extension) derived from magic bytes, or None if unsupported."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif", ".gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp", ".webp"
    # ISO base media file format (HEIC/HEIF): ....ftyp<brand>
    if len(data) >= 12 and data[4:8] == b"ftyp":
        brand = data[8:12]
        if brand in {b"heic", b"heix", b"hevc", b"hevx"}:
            return "image/heic", ".heic"
        if brand in {b"mif1", b"msf1", b"heif"}:
            return "image/heif", ".heif"
    return None


def _mime_for_key(key: str) -> str | None:
    return _EXT_TO_MIME.get(os.path.splitext(key)[1].lower())


class PhotoRepository(BaseRepository[Photo]):
    model = Photo

    async def list_for_user(self, user_id: UUID) -> list[Photo]:
        from sqlalchemy import select

        stmt = (
            select(Photo)
            .where(Photo.user_id == user_id, Photo.deleted_at.is_(None))
            .order_by(Photo.position.asc(), Photo.uploaded_at.asc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_for_user(self, photo_id: UUID, user_id: UUID) -> Photo | None:
        from sqlalchemy import select

        return await self.session.scalar(
            select(Photo).where(Photo.id == photo_id, Photo.user_id == user_id, Photo.deleted_at.is_(None))
        )


class PhotoService:
    def __init__(self, session: AsyncSession, storage: StorageBackend | None = None) -> None:
        self.session = session
        self.repo = PhotoRepository(session)
        self.storage = storage
        self.audit = AuditService(session)

    def _storage(self) -> StorageBackend:
        if self.storage is None:
            from app.services.storage import build_storage

            self.storage = build_storage()
        return self.storage

    async def request_upload(self, user: User, filename: str, content_type: str) -> tuple[str, str, int]:
        ext = os.path.splitext(filename)[1].lower()
        expected_mime = _EXT_TO_MIME.get(ext)
        if expected_mime is None or content_type != expected_mime:
            raise ValidationAppError(
                "Unsupported image format (allowed: jpeg, png, webp, gif)",
                code="UNSUPPORTED_IMAGE_TYPE",
            )
        key = new_object_key(str(user.id), filename, ext)
        upload_url = await self._storage().presigned_upload_url(key, content_type=content_type)
        return upload_url, key, 3600

    async def upload_bytes(self, user: User, data: bytes, filename: str, content_type: str) -> Photo:
        """Upload raw file bytes directly (local/S3) and register the photo.

        The stored key extension and MIME type are derived from the file's magic
        bytes; the client-supplied filename/content type are ignored.
        """
        if not data:
            raise ValidationAppError("Empty file", code="PHOTO_EMPTY")
        max_bytes = settings.MAX_PHOTO_SIZE_MB * 1024 * 1024
        if len(data) > max_bytes:
            raise ValidationAppError(
                f"Photo exceeds the {settings.MAX_PHOTO_SIZE_MB}MB limit",
                code="PHOTO_TOO_LARGE",
            )
        sniffed = _sniff_image(data)
        if sniffed is None:
            raise ValidationAppError(
                "Unsupported image format (allowed: jpeg, png, webp, gif)",
                code="UNSUPPORTED_IMAGE_TYPE",
            )
        mime, ext = sniffed
        key = new_object_key(str(user.id), filename, ext)
        await self._storage().put_object(key, data, content_type=mime)
        photo = await self.confirm_upload(user, key, content_type=mime)
        await self.audit.record(
            action="photo.upload", actor_user_id=user.id, entity_type="photo", entity_id=str(photo.id)
        )
        return photo

    async def confirm_upload(self, user: User, object_key: str, *, content_type: str | None = None) -> Photo:
        # A key is only valid for the user who owns its prefix, and the object
        # must actually exist in storage (no registering arbitrary keys).
        if not object_key.startswith(f"photos/{user.id}/"):
            raise ValidationAppError("Invalid object key", code="INVALID_OBJECT_KEY")
        key_mime = _mime_for_key(object_key)
        if key_mime is None:
            raise ValidationAppError(
                "Unsupported image format (allowed: jpeg, png, webp, gif)",
                code="UNSUPPORTED_IMAGE_TYPE",
            )
        if not await self._storage().object_exists(object_key):
            raise NotFoundError("Uploaded object not found", code="PHOTO_OBJECT_NOT_FOUND")

        photo = await self.repo.create(
            user_id=user.id,
            url=object_key,
            thumbnail_url=None,
            position=0,
            is_profile_photo=False,
        )
        # Never persist a client-supplied MIME type outside the allowlist.
        if content_type in _EXT_TO_MIME.values():
            photo.mime_type = content_type
        else:
            photo.mime_type = key_mime
        return photo

    async def list(self, user: User) -> list[Photo]:
        return await self.repo.list_for_user(user.id)

    async def to_public_url(self, url: str | None) -> str | None:
        if not url:
            return None
        if url.startswith("http") or url.startswith("/static/"):
            return url
        return await self._storage().presigned_download_url(url)

    async def update(self, user: User, photo_id: UUID, data: dict[str, Any]) -> Photo:
        photo = await self.repo.get_for_user(photo_id, user.id)
        if photo is None:
            raise NotFoundError("Photo not found", code="PHOTO_NOT_FOUND")
        if "position" in data and data["position"] is not None:
            photo.position = data["position"]
        if "is_profile_photo" in data and data["is_profile_photo"] is True:
            await self._clear_profile_photo(user.id)
            photo.is_profile_photo = True
        if "visibility" in data and data["visibility"] is not None:
            photo.visibility = data["visibility"]
        await self.audit.record(
            action="photo.update", actor_user_id=user.id, entity_type="photo", entity_id=str(photo.id)
        )
        return photo

    async def delete(self, user: User, photo_id: UUID) -> None:
        photo = await self.repo.get_for_user(photo_id, user.id)
        if photo is None:
            raise NotFoundError("Photo not found", code="PHOTO_NOT_FOUND")
        photo.deleted_at = self._now()
        await self.audit.record(
            action="photo.delete", actor_user_id=user.id, entity_type="photo", entity_id=str(photo.id)
        )

    async def _clear_profile_photo(self, user_id: UUID) -> None:
        photos = await self.repo.list_for_user(user_id)
        for p in photos:
            p.is_profile_photo = False

    # ---------- admin moderation ----------

    async def admin_list(
        self,
        *,
        status: PhotoVerificationStatus | None = None,
        user_id: UUID | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[builtins.list[dict], int]:
        from app.db.models import Profile

        stmt = (
            select(Photo, Profile.first_name, Profile.last_name, User.email)
            .outerjoin(Profile, Profile.user_id == Photo.user_id)
            .outerjoin(User, User.id == Photo.user_id)
            .where(Photo.deleted_at.is_(None))
        )
        count_stmt = select(func.count()).select_from(Photo).where(Photo.deleted_at.is_(None))
        if status is not None:
            stmt = stmt.where(Photo.verification_status == status)
            count_stmt = count_stmt.where(Photo.verification_status == status)
        if user_id is not None:
            stmt = stmt.where(Photo.user_id == user_id)
            count_stmt = count_stmt.where(Photo.user_id == user_id)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(User.email.ilike(like))
            count_stmt = count_stmt.where(User.email.ilike(like))
        total = int((await self.session.execute(count_stmt)).scalar_one())
        rows = (await self.session.execute(stmt.order_by(Photo.uploaded_at.desc()).limit(limit).offset(offset))).all()
        return (
            [
                {
                    "id": str(ph.id),
                    "user_id": str(ph.user_id),
                    "user_name": " ".join(n for n in (first, last) if n) or None,
                    "url": ph.url,
                    "thumbnail_url": ph.thumbnail_url,
                    "verification_status": ph.verification_status.value,
                    "mime_type": ph.mime_type,
                    "is_profile_photo": ph.is_profile_photo,
                    "uploaded_at": ph.uploaded_at,
                    "created_at": ph.created_at,
                }
                for ph, first, last, _email in rows
            ],
            total,
        )

    async def review(
        self,
        admin: User,
        photo_id: UUID,
        *,
        action: str,
        reason: str | None = None,
    ) -> Photo:
        if action not in {"approve", "reject", "request_replacement"}:
            raise ValidationAppError("action must be approve|reject|request_replacement", code="INVALID_ACTION")
        photo = await self.session.scalar(select(Photo).where(Photo.id == photo_id, Photo.deleted_at.is_(None)))
        if photo is None:
            raise NotFoundError("Photo not found", code="PHOTO_NOT_FOUND")
        if action == "approve":
            photo.verification_status = PhotoVerificationStatus.VERIFIED
        else:
            photo.verification_status = PhotoVerificationStatus.REJECTED
        await self.audit.record(
            action=f"photo.{action}",
            actor_user_id=admin.id,
            entity_type="photo",
            entity_id=str(photo.id),
            metadata={"reason": reason},
        )
        return photo

    @staticmethod
    def _now():
        from datetime import datetime

        return datetime.now(UTC)
