from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    PartnerPreference,
    PreferredCaste,
    PreferredCountry,
    PreferredDiet,
    PreferredJunctionBase,
    PreferredLanguage,
    PreferredReligion,
    PreferredState,
)

JUNCTION_MODELS: dict[str, tuple[type[PreferredJunctionBase], str]] = {
    "preferred_religions": (PreferredReligion, "religion"),
    "preferred_castes": (PreferredCaste, "caste"),
    "preferred_languages": (PreferredLanguage, "language"),
    "preferred_countries": (PreferredCountry, "country"),
    "preferred_states": (PreferredState, "state"),
    "preferred_diets": (PreferredDiet, "diet"),
}


class PreferenceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: UUID) -> PartnerPreference:
        pref = await self.session.scalar(select(PartnerPreference).where(PartnerPreference.user_id == user_id))
        if pref is None:
            pref = PartnerPreference(user_id=user_id)
            self.session.add(pref)
            await self.session.flush()
        return pref

    async def update(self, user_id: UUID, data: dict) -> PartnerPreference:
        pref = await self.get(user_id)
        scalar_fields = {
            "age_min",
            "age_max",
            "height_min_cm",
            "height_max_cm",
            "preferred_marital_status",
            "preferred_physical_status",
            "preferred_family_values",
            "preferred_education",
            "preferred_employed_in",
        }
        for field, value in data.items():
            if field in scalar_fields and value is not None or field.endswith("_level") and value is not None:
                setattr(pref, field, value)

        for field, (model, attr) in JUNCTION_MODELS.items():
            items = data.get(field)
            if items is None:
                continue
            await self.session.execute(delete(model).where(model.preference_id == pref.id))
            for item in items:
                level = item.get("level", "PREFERRED")
                if level == "NO_PREFERENCE":
                    continue
                await self.session.flush()
                self.session.add(model(preference_id=pref.id, **{attr: item["value"]}, level=level))
        await self.session.flush()
        return pref

    async def serialize(self, user_id: UUID) -> dict[str, Any]:
        pref = await self.get(user_id)
        result: dict[str, Any] = {
            "age_min": pref.age_min,
            "age_max": pref.age_max,
            "height_min_cm": pref.height_min_cm,
            "height_max_cm": pref.height_max_cm,
            "preferred_marital_status": pref.preferred_marital_status,
            "preferred_physical_status": pref.preferred_physical_status,
            "preferred_family_values": pref.preferred_family_values,
            "preferred_education": pref.preferred_education,
            "preferred_employed_in": pref.preferred_employed_in,
        }
        for field, (model, attr) in JUNCTION_MODELS.items():
            rows = await self.session.execute(select(model).where(model.preference_id == pref.id))
            result[field] = [{"value": getattr(r, attr), "level": r.level} for r in rows.scalars().all()]
        return result

    async def hard_filters(self, user_id: UUID) -> dict:
        """Extract REQUIRED filters for recommendation hard-filtering."""
        pref = await self.get(user_id)
        filters: dict = {"age_min": pref.age_min, "age_max": pref.age_max}
        if pref.religion_level == "REQUIRED":
            rows = await self.session.execute(
                select(PreferredReligion.religion).where(PreferredReligion.preference_id == pref.id)
            )
            filters["religions"] = list(rows.scalars().all())
        if pref.caste_level == "REQUIRED":
            rows = await self.session.execute(
                select(PreferredCaste.caste).where(PreferredCaste.preference_id == pref.id)
            )
            filters["castes"] = list(rows.scalars().all())
        if pref.country_level == "REQUIRED":
            rows = await self.session.execute(
                select(PreferredCountry.country).where(PreferredCountry.preference_id == pref.id)
            )
            filters["countries"] = list(rows.scalars().all())
        return filters

    async def soft_preferences(self, user_id: UUID) -> dict:
        """Extract PREFERRED items for scoring."""
        pref = await self.get(user_id)
        out: dict = {}
        for field, (model, attr) in JUNCTION_MODELS.items():
            rows = await self.session.execute(
                select(model).where(model.preference_id == pref.id, model.level == "PREFERRED")
            )
            out[field] = [getattr(r, attr) for r in rows.scalars().all()]
        return out
