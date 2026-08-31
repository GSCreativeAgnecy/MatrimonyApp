from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, JSONBType, TimestampMixin, UTCDateTime, enum_column, gen_uuid
from app.db.enums import AstrologyRashi, Dosham, Nakshatra


class AstrologyProfile(Base, TimestampMixin):
    __tablename__ = "astrology_profiles"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    time_of_birth: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    place_of_birth: Mapped[str | None] = mapped_column(nullable=True)

    birth_lat: Mapped[float | None] = mapped_column(nullable=True)
    birth_lng: Mapped[float | None] = mapped_column(nullable=True)
    birth_timezone: Mapped[str | None] = mapped_column(nullable=True)

    rashi: Mapped[AstrologyRashi] = enum_column(AstrologyRashi, nullable=True, index=True)
    nakshatra: Mapped[Nakshatra] = enum_column(Nakshatra, nullable=True)
    gothram: Mapped[str | None] = mapped_column(nullable=True)
    dosham: Mapped[Dosham] = enum_column(Dosham, default=Dosham.NONE, nullable=True)

    horoscope_data: Mapped[dict | None] = mapped_column(JSONBType, nullable=True, default=dict)

    horoscope_verified: Mapped[bool] = mapped_column(default=False, nullable=False)

    __table_args__ = (
        CheckConstraint("birth_lat IS NULL OR (birth_lat BETWEEN -90 AND 90)", name="birth_lat_range"),
        CheckConstraint("birth_lng IS NULL OR (birth_lng BETWEEN -180 AND 180)", name="birth_lng_range"),
    )
