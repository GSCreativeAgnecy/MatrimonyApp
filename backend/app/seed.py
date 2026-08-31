"""Idempotent seed script.

Usage:
    python -m app.seed

Seeds lookup data (languages, religions, castes, countries, states, education,
occupations, interests), subscription plans, and the remote app configuration
key registry. Safe to run repeatedly — it never duplicates rows and never
overwrites admin-edited configuration.
"""

import asyncio
import os
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import AccountStatus, UserRole
from app.db.models import (
    AppConfig,
    Caste,
    Country,
    EducationLevel,
    Interest,
    Language,
    Occupation,
    Religion,
    RolePermission,
    State,
    SubscriptionPlan,
    User,
)
from app.db.session import SessionLocal
from app.security.password import hash_password
from app.security.permissions import ROLE_PERMISSIONS
from app.services.app_config_keys import CONFIG_KEY_SPECS

LANGUAGES = [
    ("en", "English"),
    ("hi", "Hindi"),
    ("bn", "Bengali"),
    ("ta", "Tamil"),
    ("te", "Telugu"),
    ("kn", "Kannada"),
    ("ml", "Malayalam"),
    ("mr", "Marathi"),
    ("gu", "Gujarati"),
    ("pa", "Punjabi"),
    ("or", "Odia"),
    ("ur", "Urdu"),
]

RELIGIONS = ["Hindu", "Muslim", "Christian", "Sikh", "Jain", "Buddhist", "Parsi", "Other"]

CASTES = {
    "Hindu": [
        "Brahmin",
        "Kshatriya",
        "Vaishya",
        "Shudra",
        "Rajput",
        "Maratha",
        "Reddy",
        "Nair",
        "Iyer",
        "Jat",
        "Baniya",
        "Other",
    ],
    "Muslim": ["Sunni", "Shia", "Other"],
    "Christian": ["Catholic", "Protestant", "Syrian Christian", "Other"],
    "Sikh": ["Jat Sikh", "Khatri", "Arora", "Other"],
    "Jain": ["Digambara", "Shwetambara", "Other"],
}

COUNTRIES = [
    ("IN", "India"),
    ("US", "United States"),
    ("GB", "United Kingdom"),
    ("CA", "Canada"),
    ("AU", "Australia"),
    ("AE", "United Arab Emirates"),
    ("SG", "Singapore"),
]

INDIA_STATES = [
    "Andhra Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Delhi",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Tamil Nadu",
    "Telangana",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
]

EDUCATION_LEVELS = [
    "High School",
    "Diploma",
    "Bachelor's Degree",
    "Master's Degree",
    "Doctorate",
    "Professional Degree",
]

OCCUPATIONS = [
    "Software Engineer",
    "Doctor",
    "Lawyer",
    "Teacher",
    "Business Owner",
    "Accountant",
    "Architect",
    "Civil Engineer",
    "Nurse",
    "Marketing Manager",
    "Consultant",
    "Data Scientist",
    "Financial Analyst",
    "Government Employee",
    "Retired",
    "Homemaker",
]

INTERESTS = [
    ("sports", "Sports"),
    ("travel", "Travel"),
    ("cooking", "Cooking"),
    ("music", "Music"),
    ("movies", "Movies"),
    ("reading", "Reading"),
    ("fitness", "Fitness"),
    ("pets", "Pets"),
    ("volunteering", "Volunteering"),
    ("yoga", "Yoga"),
    ("photography", "Photography"),
    ("dance", "Dance"),
]

PLANS = [
    {
        "name": "Premium Plus",
        "description": "Unlimited likes, see who liked you, priority profile.",
        "price": Decimal("1999.00"),
        "currency": "INR",
        "duration_days": 90,
        "features": {"unlimited_likes": True, "see_who_liked_you": True, "priority": True},
    },
    {
        "name": "Premium",
        "description": "See who liked you and message all matches.",
        "price": Decimal("999.00"),
        "currency": "INR",
        "duration_days": 30,
        "features": {"unlimited_likes": False, "see_who_liked_you": True, "priority": False},
    },
]


async def _get_or_create(session: AsyncSession, model, *, lookup: dict, create: dict) -> tuple[object, bool]:
    obj = await session.scalar(select(model).where(*[getattr(model, k) == v for k, v in lookup.items()]))
    if obj is None:
        obj = model(**{**lookup, **create})
        session.add(obj)
        await session.flush()
        return obj, True
    return obj, False


async def seed(session: AsyncSession) -> int:
    created = 0

    for code, name in LANGUAGES:
        _, is_new = await _get_or_create(session, Language, lookup={"code": code}, create={"name": name})
        created += 1 if is_new else 0
    for name in RELIGIONS:
        _, is_new = await _get_or_create(session, Religion, lookup={"name": name}, create={})
        created += 1 if is_new else 0
    for religion, castes in CASTES.items():
        for caste in castes:
            _, is_new = await _get_or_create(session, Caste, lookup={"religion": religion, "name": caste}, create={})
            created += 1 if is_new else 0
    for code, name in COUNTRIES:
        _, is_new = await _get_or_create(session, Country, lookup={"code": code}, create={"name": name})
        created += 1 if is_new else 0
    for state in INDIA_STATES:
        _, is_new = await _get_or_create(session, State, lookup={"country_code": "IN", "name": state}, create={})
        created += 1 if is_new else 0
    for name in EDUCATION_LEVELS:
        _, is_new = await _get_or_create(session, EducationLevel, lookup={"name": name}, create={})
        created += 1 if is_new else 0
    for name in OCCUPATIONS:
        _, is_new = await _get_or_create(session, Occupation, lookup={"name": name}, create={})
        created += 1 if is_new else 0
    for slug, name in INTERESTS:
        _, is_new = await _get_or_create(session, Interest, lookup={"slug": slug}, create={"name": name})
        created += 1 if is_new else 0

    for plan in PLANS:
        _, is_new = await _get_or_create(session, SubscriptionPlan, lookup={"name": plan["name"]}, create=plan)
        created += 1 if is_new else 0

    # Remote app configuration (idempotent; existing rows are left untouched so
    # admin edits are never overwritten by a re-run).
    #
    # Specs whose default is None are intentionally NOT seeded: ``app_config.value``
    # is NOT NULL, and the public/admin config response already falls back to the
    # schema defaults for missing keys, so the key simply stays unset until an
    # admin sets it.
    for spec in CONFIG_KEY_SPECS.values():
        if spec.default is None:
            continue
        _, is_new = await _get_or_create(
            session,
            AppConfig,
            lookup={"key": spec.key},
            create={
                "value": spec.default,
                "value_type": spec.value_type,
                "category": spec.category,
                "is_public": spec.is_public,
                "is_active": True,
                "description": spec.description,
            },
        )
        created += 1 if is_new else 0

    # Role -> permission registry (idempotent; runtime overrides survive re-runs).
    created += await _seed_role_permissions(session)

    # Development-only admin. Only created when explicitly configured; the
    # password comes from the environment and is never logged or committed.
    created += await _seed_dev_admin(session)

    await session.commit()
    return created


async def _seed_role_permissions(session: AsyncSession) -> int:
    """Seed the role -> permission registry in bulk (one read, one insert)."""
    existing = set(
        (await session.execute(select(RolePermission.role, RolePermission.permission))).all()
    )
    to_add: list[RolePermission] = []
    for role, permissions in ROLE_PERMISSIONS.items():
        for permission in permissions:
            if (role.value, permission) not in existing:
                to_add.append(RolePermission(role=role.value, permission=permission))
    session.add_all(to_add)
    await session.flush()
    return len(to_add)


async def _seed_dev_admin(session: AsyncSession) -> int:
    email = os.getenv("DEV_ADMIN_EMAIL")
    password = os.getenv("DEV_ADMIN_PASSWORD")
    if not email or not password:
        return 0
    if len(password) < 8 or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
        raise ValueError("DEV_ADMIN_PASSWORD must be at least 8 chars with an uppercase letter and a digit")
    existing = await session.scalar(select(User).where(User.email == email))
    if existing is not None:
        return 0
    session.add(
        User(
            email=email.lower(),
            password_hash=hash_password(password),
            account_status=AccountStatus.ACTIVE,
            role=UserRole.SUPER_ADMIN,
            email_verified_at=None,
        )
    )
    await session.flush()
    print(f"Created development admin for {email} (SUPER_ADMIN).")  # noqa: T201
    return 1


async def main() -> None:
    async with SessionLocal() as session:
        n = await seed(session)
        print(f"Seed complete. (new rows: {n})")


if __name__ == "__main__":
    asyncio.run(main())
