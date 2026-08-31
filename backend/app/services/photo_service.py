import builtins
import os
from datetime import UTC
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import NotFoundError, ValidationAppError
from app.db.enums import PhotoVerificationStatus
from app.db.models import Photo, User
from app.repositories.base import BaseRepository
from app.services.audit_service import AuditService
from app.services.storage import StorageBackend, new_object_key


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
        key = new_object_key(str(user.id), filename, os.path.splitext(filename)[1])
        upload_url = await self._storage().presigned_upload_url(key, content_type=content_type)
        return upload_url, key, 3600

    async def confirm_upload(self, user: User, object_key: str, *, content_type: str | None = None) -> Photo:
        photo = await self.repo.create(
            user_id=user.id,
            url=object_key,
            thumbnail_url=None,
            position=0,
            is_profile_photo=False,
        )
        if content_type:
            photo.mime_type = content_type
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
