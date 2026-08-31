from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class AstrologyProvider(Protocol):
    """Abstraction over astrology vendors/calculators.

    The rest of the system depends only on this protocol, so a real provider
    (e.g. Drik Panchang / AstroSage APIs) can be added without rewrites.
    """

    async def calculate_chart(
        self,
        *,
        birth_datetime: datetime | None = None,
        birth_lat: float | None = None,
        birth_lng: float | None = None,
        birth_timezone: str | None = None,
    ) -> dict | None:
        """Return a dict with keys: rashi, nakshatra, gothram, dosham, horoscope_data."""
        ...


class NoopAstrologyProvider:
    """Default provider that returns no data (horoscope entry stays manual)."""

    async def calculate_chart(
        self,
        *,
        birth_datetime: datetime | None = None,
        birth_lat: float | None = None,
        birth_lng: float | None = None,
        birth_timezone: str | None = None,
    ) -> dict | None:
        return None
