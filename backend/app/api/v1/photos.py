from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.db.models import User
from app.schemas.common import ApiResponse
from app.schemas.photo import (
    PhotoResponse,
    PhotoUpdate,
    PhotoUploadUrlRequest,
    PhotoUploadUrlResponse,
)
from app.services.photo_service import PhotoService

router = APIRouter(prefix="/profile/photos", tags=["photos"])


def _serialize_photos(service: PhotoService, photos: list) -> list[dict]:
    result = []
    for p in photos:
        result.append(
            {
                "id": str(p.id),
                "url": p.url,
                "thumbnail_url": p.thumbnail_url,
                "position": p.position,
                "is_profile_photo": p.is_profile_photo,
                "verification_status": p.verification_status.value,
                "visibility": p.visibility.value,
                "uploaded_at": p.uploaded_at.isoformat() if p.uploaded_at else None,
            }
        )
    return result


@router.get("", summary="List my photos", response_model=ApiResponse[list[PhotoResponse]])
async def list_photos(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[list[PhotoResponse]]:
    service = PhotoService(session)
    photos = await service.list(user)
    return ApiResponse(data=_serialize_photos(service, photos))


@router.post("/upload-url", summary="Request a signed upload URL", response_model=ApiResponse[PhotoUploadUrlResponse])
async def request_upload_url(
    payload: PhotoUploadUrlRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[PhotoUploadUrlResponse]:
    service = PhotoService(session)
    upload_url, object_key, expires_in = await service.request_upload(user, payload.filename, payload.content_type)
    return ApiResponse(
        data=PhotoUploadUrlResponse(upload_url=upload_url, object_key=object_key, expires_in=expires_in)
    )


@router.post("/confirm", summary="Confirm an upload and register the photo", response_model=ApiResponse[PhotoResponse])
async def confirm_upload(
    payload: dict,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[PhotoResponse]:
    service = PhotoService(session)
    photo = await service.confirm_upload(user, payload["object_key"], content_type=payload.get("content_type"))
    await session.commit()
    data = _serialize_photos(service, [photo])[0]
    return ApiResponse(data=data)


@router.patch(
    "/{photo_id}",
    summary="Update a photo (order / profile photo / visibility)",
    response_model=ApiResponse[PhotoResponse],
)
async def update_photo(
    photo_id: UUID,
    body: PhotoUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[PhotoResponse]:
    service = PhotoService(session)
    photo = await service.update(user, photo_id, body.model_dump(exclude_unset=True))
    await session.commit()
    data = _serialize_photos(service, [photo])[0]
    return ApiResponse(data=data)


@router.delete("/{photo_id}", summary="Delete a photo", response_model=ApiResponse[dict])
async def delete_photo(
    photo_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    service = PhotoService(session)
    await service.delete(user, photo_id)
    await session.commit()
    return ApiResponse(data={"status": "deleted"})
