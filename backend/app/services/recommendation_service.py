"""Deterministic recommendation pipeline.

    Candidate Generation -> Hard Filters -> Compatibility Scoring -> Ranking -> Feed

The `ScoringEngine` is a replaceable protocol so an ML model can be swapped in later.
"""

from typing import Any, Protocol

from app.db.models import Profile, User
from app.repositories.match_repo import MatchRepository
from app.repositories.moderation_repo import BlockRepository
from app.repositories.profile_repo import ProfileRepository
from app.repositories.swipe_repo import SwipeRepository


class ScoringEngine(Protocol):
    def score(self, viewer: dict[str, Any], candidate: dict[str, Any], preferences: dict[str, Any]) -> dict[str, Any]:
        """Return {"score": float, "reason_codes": list[str]}."""
        ...


WEIGHTS: dict[str, float] = {
    "age": 0.14,
    "height": 0.04,
    "location": 0.10,
    "religion": 0.10,
    "caste": 0.08,
    "language": 0.08,
    "education": 0.08,
    "occupation": 0.06,
    "diet": 0.06,
    "smoking": 0.05,
    "drinking": 0.05,
    "family": 0.05,
    "interests": 0.06,
    "marital": 0.03,
    "intent": 0.02,
}

_REASON_MAP = {
    "age": "AGE_MATCH",
    "height": "HEIGHT_MATCH",
    "location": "LOCATION_MATCH",
    "religion": "RELIGION_MATCH",
    "caste": "CASTE_MATCH",
    "language": "LANGUAGE_MATCH",
    "education": "EDUCATION_MATCH",
    "occupation": "OCCUPATION_MATCH",
    "diet": "DIET_MATCH",
    "smoking": "SMOKING_MATCH",
    "drinking": "DRINKING_MATCH",
    "family": "FAMILY_VALUES_MATCH",
    "interests": "SHARED_INTERESTS",
    "marital": "MARITAL_STATUS_MATCH",
    "intent": "INTENT_MATCH",
}


def _approx(x: Any, y: Any, tolerance: float = 0.0) -> bool:
    return x is not None and y is not None and abs(x - y) <= tolerance


class DeterministicScoringEngine:
    def score(self, viewer: dict[str, Any], candidate: dict[str, Any], preferences: dict[str, Any]) -> dict[str, Any]:
        total = 0.0
        codes: list[str] = []

        def add(factor: str, sub_score: float, reason: bool) -> None:
            nonlocal total
            total += WEIGHTS[factor] * max(0.0, min(1.0, sub_score))
            if reason and sub_score >= 0.7:
                codes.append(_REASON_MAP[factor])

        # Age
        v_age = viewer.get("age")
        c_age = candidate.get("age")
        if v_age is not None and c_age is not None:
            pref = preferences.get("pref", {})
            lo, hi = pref.get("age_min"), pref.get("age_max")
            if lo is not None and hi is not None and lo <= c_age <= hi:
                add("age", 1.0, True)
            else:
                diff = abs(v_age - c_age)
                add("age", max(0.0, 1.0 - diff / 20), False)
        else:
            add("age", 0.5, False)

        # Height
        if _approx(viewer.get("height_cm"), candidate.get("height_cm"), 5):
            add("height", 1.0, True)
        elif candidate.get("height_cm") is not None:
            add("height", 0.4, False)
        else:
            add("height", 0.5, False)

        # Location
        v_loc = (viewer.get("country"), viewer.get("state"), viewer.get("city"))
        c_loc = (candidate.get("country"), candidate.get("state"), candidate.get("city"))
        if v_loc == c_loc and any(v_loc):
            add("location", 1.0, True)
        elif v_loc[0:2] == c_loc[0:2] and v_loc[0]:
            add("location", 0.8, True)
        elif v_loc[0] and v_loc[0] == c_loc[0]:
            add("location", 0.5, False)
        else:
            add("location", 0.3, False)

        # Religion / caste / language / education / occupation
        for field, weight_key, reason in (
            ("religion", "religion", True),
            ("caste", "caste", True),
            ("mother_tongue", "language", True),
            ("education", "education", True),
            ("occupation", "occupation", True),
        ):
            v = viewer.get(field)
            c = candidate.get(field)
            if v and c:
                add(weight_key, 1.0 if str(v).lower() == str(c).lower() else 0.0, reason)
            else:
                add(weight_key, 0.5, False)

        # Diet / smoking / drinking / family / marital / intent
        for field, weight_key in (
            ("diet", "diet"),
            ("smoking", "smoking"),
            ("drinking", "drinking"),
            ("family_values", "family"),
            ("marital_status", "marital"),
            ("intent", "intent"),
        ):
            v = viewer.get(field)
            c = candidate.get(field)
            if v and c:
                add(weight_key, 1.0 if v == c else 0.0, weight_key in ("diet", "marital", "intent"))
            else:
                add(weight_key, 0.5, False)

        # Interests overlap
        v_ints = set(viewer.get("interests") or [])
        c_ints = set(candidate.get("interests") or [])
        if v_ints and c_ints:
            overlap = len(v_ints & c_ints) / max(len(v_ints | c_ints), 1)
            add("interests", overlap, True)
        else:
            add("interests", 0.5, False)

        return {"score": round(total * 100, 1), "reason_codes": codes}


class RecommendationService:
    def __init__(self, session) -> None:
        self.session = session
        self.profiles = ProfileRepository(session)
        self.swipes = SwipeRepository(session)
        self.matches = MatchRepository(session)
        self.blocks = BlockRepository(session)
        self.engine: ScoringEngine = DeterministicScoringEngine()

    async def _viewer_payload(self, viewer: User, profile: Profile) -> dict[str, Any]:
        from app.services.profile_service import _age

        interests = await self._interests(viewer.id)
        return {
            "age": _age(profile.date_of_birth),
            "height_cm": profile.height_cm,
            "country": profile.country,
            "state": profile.state,
            "city": profile.city,
            "religion": profile.religion,
            "caste": profile.caste,
            "mother_tongue": profile.mother_tongue,
            "education": profile.education,
            "occupation": profile.occupation,
            "diet": profile.diet.value if profile.diet else None,
            "smoking": profile.smoking.value if profile.smoking else None,
            "drinking": profile.drinking.value if profile.drinking else None,
            "family_values": None,
            "marital_status": profile.marital_status.value if profile.marital_status else None,
            "intent": profile.intent.value if profile.intent else None,
            "interests": interests,
        }

    async def _interests(self, user_id) -> list[str]:
        from sqlalchemy import select

        from app.db.models import Interest, UserInterest

        stmt = (
            select(Interest.slug)
            .join(UserInterest, UserInterest.interest_id == Interest.id)
            .where(UserInterest.user_id == user_id)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def _candidates(self, viewer: User) -> list[Profile]:
        blocked = set(await self.blocks.blocked_ids(viewer.id)) | set(await self.blocks.who_blocked_me(viewer.id))
        swiped = set(await self.swipes.swiped_user_ids(viewer.id))
        matched = set(await self.matches.active_match_ids_for(viewer.id))
        matched_ids: set = set()
        if matched:
            from sqlalchemy import select

            from app.db.models import Match

            stmt = select(Match).where(Match.id.in_(matched))
            rows = (await self.session.execute(stmt)).scalars().all()
            for m in rows:
                matched_ids.add(m.user1_id)
                matched_ids.add(m.user2_id)
        matched_ids.discard(viewer.id)

        excluded = blocked | swiped | matched_ids
        stmt = self.profiles.discovery_base_query(viewer.id)
        if excluded:
            stmt = stmt.where(Profile.user_id.not_in(excluded))
        profiles = (await self.session.execute(stmt)).scalars().all()
        return list(profiles)

    async def _preferences(self, viewer_id) -> dict[str, Any]:
        from app.services.preference_service import PreferenceService

        ps = PreferenceService(self.session)
        return {
            "pref": await ps.hard_filters(viewer_id),
            "soft": await ps.soft_preferences(viewer_id),
        }

    async def build_feed(self, viewer: User, *, limit: int = 20, cursor: str | None = None) -> dict:
        key = f"recs:{viewer.id}"
        items = await self._load_cached(key)
        if items is None:
            items = await self._compute_feed(viewer)
            await self._cache(key, items)

        start = int(cursor) if cursor and cursor.isdigit() else 0
        page = items[start : start + limit]
        next_cursor = str(start + limit) if start + limit < len(items) else None
        return {
            "items": page,
            "next_cursor": next_cursor,
            "has_more": next_cursor is not None,
        }

    async def _compute_feed(self, viewer: User) -> list[dict]:
        candidates = await self._candidates(viewer)
        viewer_profile = await self.profiles.get_by_user(viewer.id)
        if viewer_profile is None:
            return []
        viewer_payload = await self._viewer_payload(viewer, viewer_profile)
        preferences = await self._preferences(viewer.id)

        results: list[dict] = []
        for cand in candidates:
            cand_payload = await self._viewer_payload_from_profile(cand)
            scored = self.engine.score(viewer_payload, cand_payload, preferences)
            results.append(
                {
                    "candidate_user_id": str(cand.user_id),
                    "score": scored["score"],
                    "reason_codes": scored["reason_codes"],
                }
            )
        results.sort(key=lambda r: r["score"], reverse=True)
        return results

    async def _viewer_payload_from_profile(self, profile: Profile) -> dict[str, Any]:
        from app.services.profile_service import _age

        interests = await self._interests(profile.user_id)
        return {
            "age": _age(profile.date_of_birth),
            "height_cm": profile.height_cm,
            "country": profile.country,
            "state": profile.state,
            "city": profile.city,
            "religion": profile.religion,
            "caste": profile.caste,
            "mother_tongue": profile.mother_tongue,
            "education": profile.education,
            "occupation": profile.occupation,
            "diet": profile.diet.value if profile.diet else None,
            "smoking": profile.smoking.value if profile.smoking else None,
            "drinking": profile.drinking.value if profile.drinking else None,
            "family_values": None,
            "marital_status": profile.marital_status.value if profile.marital_status else None,
            "intent": profile.intent.value if profile.intent else None,
            "interests": interests,
        }

    # ---------- cache ----------

    async def _load_cached(self, key: str) -> list[dict] | None:
        try:
            from app.security.redis import get_redis

            redis = await get_redis()
            raw = await redis.get(key)
            if raw:
                import json

                return json.loads(raw)
        except Exception:
            return None
        return None

    async def _cache(self, key: str, items: list[dict], ttl: int = 900) -> None:
        try:
            import json

            from app.security.redis import get_redis

            redis = await get_redis()
            await redis.setex(key, ttl, json.dumps(items))
        except Exception:
            pass
