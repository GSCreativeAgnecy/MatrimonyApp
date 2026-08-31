from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AstrologyProfile
from app.repositories.base import BaseRepository


class AstrologyRepository(BaseRepository[AstrologyProfile]):
    model = AstrologyProfile

    async def get_for_user(self, user_id: UUID) -> AstrologyProfile | None:
        return await self.session.scalar(select(AstrologyProfile).where(AstrologyProfile.user_id == user_id))


class AstrologyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AstrologyRepository(session)

    async def get(self, user_id: UUID) -> AstrologyProfile:
        profile = await self.repo.get_for_user(user_id)
        if profile is None:
            profile = AstrologyProfile(user_id=user_id)
            self.session.add(profile)
            await self.session.flush()
        return profile

    async def update(self, user_id: UUID, data: dict) -> AstrologyProfile:
        profile = await self.get(user_id)
        fields = {
            "time_of_birth",
            "place_of_birth",
            "birth_lat",
            "birth_lng",
            "birth_timezone",
            "rashi",
            "nakshatra",
            "gothram",
            "dosham",
        }
        for field in fields:
            value = data.get(field)
            if value is not None:
                setattr(profile, field, value)
        return profile

    async def calculate_chart(self, user_id: UUID) -> AstrologyProfile:
        """Fetches/calculates horoscope via a pluggable provider (default: no-op provider)."""

        provider: AstrologyProvider = ProviderRegistry.default()
        profile = await self.get(user_id)
        result = provider.calculate_chart(
            birth_datetime=profile.time_of_birth,
            birth_lat=profile.birth_lat,
            birth_lng=profile.birth_lng,
            birth_timezone=profile.birth_timezone,
        )
        if result:
            profile.rashi = result.get("rashi") or profile.rashi
            profile.nakshatra = result.get("nakshatra") or profile.nakshatra
            profile.gothram = result.get("gothram") or profile.gothram
            profile.dosham = result.get("dosham") or profile.dosham
            profile.horoscope_data = result.get("horoscope_data") or profile.horoscope_data
        return profile


class ProviderRegistry:
    """Simple registry so a real astrology vendor can be plugged in via config."""

    _default: AstrologyProvider | None = None

    @classmethod
    def default(cls) -> AstrologyProvider:
        if cls._default is None:
            cls._default = NoopAstrologyProvider()
        return cls._default


class AstrologyProvider:
    def calculate_chart(
        self,
        *,
        birth_datetime=None,
        birth_lat: float | None = None,
        birth_lng: float | None = None,
        birth_timezone: str | None = None,
    ) -> dict | None:
        raise NotImplementedError


class NoopAstrologyProvider(AstrologyProvider):
    def calculate_chart(self, *, birth_datetime=None, birth_lat=None, birth_lng=None, birth_timezone=None):
        return None
