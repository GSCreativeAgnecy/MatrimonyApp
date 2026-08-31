from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.enums import PhotoVerificationStatus, PhotoVisibility


class PhotoUploadUrlRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str

    @field_validator("content_type")
    @classmethod
    def _allowed_types(cls, v: str) -> str:
        allowed = {"image/jpeg", "image/png", "image/webp", "image/heic"}
        if v not in allowed:
            raise ValueError(f"Unsupported content type: {v}")
        return v


class PhotoUploadUrlResponse(BaseModel):
    upload_url: str
    object_key: str
    expires_in: int


class PhotoCreate(BaseModel):
    url: str
    thumbnail_url: str | None = None
    position: int = 0
    is_profile_photo: bool = False
    visibility: PhotoVisibility = PhotoVisibility.PUBLIC


class PhotoUpdate(BaseModel):
    position: int | None = None
    is_profile_photo: bool | None = None
    visibility: PhotoVisibility | None = None


class PhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    url: str
    thumbnail_url: str | None = None
    position: int
    is_profile_photo: bool
    verification_status: PhotoVerificationStatus
    visibility: PhotoVisibility
    uploaded_at: str | None = None
