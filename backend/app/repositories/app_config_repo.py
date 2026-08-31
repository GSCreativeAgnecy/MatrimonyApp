from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select

from app.db.enums import ConfigCategory
from app.db.models import AppConfig
from app.repositories.base import BaseRepository


class AppConfigRepository(BaseRepository[AppConfig]):
    model = AppConfig

    async def get_by_key(self, key: str) -> AppConfig | None:
        return await self.session.scalar(select(AppConfig).where(AppConfig.key == key))

    async def list_configs(
        self,
        *,
        category: ConfigCategory | None = None,
        is_public: bool | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AppConfig]:
        stmt = select(AppConfig).order_by(AppConfig.category, AppConfig.key)
        if category is not None:
            stmt = stmt.where(AppConfig.category == category)
        if is_public is not None:
            stmt = stmt.where(AppConfig.is_public.is_(is_public))
        if is_active is not None:
            stmt = stmt.where(AppConfig.is_active.is_(is_active))
        stmt = stmt.limit(limit).offset(offset)
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_public_active(self) -> list[AppConfig]:
        stmt = (
            select(AppConfig)
            .where(AppConfig.is_public.is_(True), AppConfig.is_active.is_(True))
            .order_by(AppConfig.category, AppConfig.key)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def create_config(
        self,
        *,
        key: str,
        value: Any,
        value_type: str,
        category: str,
        is_public: bool,
        is_active: bool,
        description: str | None,
        updated_by: UUID | None,
    ) -> AppConfig:
        return await self.create(
            key=key,
            value=value,
            value_type=value_type,
            category=category,
            is_public=is_public,
            is_active=is_active,
            description=description,
            updated_by=updated_by,
        )

    async def latest_updated_at(self) -> datetime | None:
        stmt = select(func.max(AppConfig.updated_at))
        return await self.session.scalar(stmt)
