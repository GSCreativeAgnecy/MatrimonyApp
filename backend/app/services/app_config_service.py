"""Remote app configuration service.

Business rules for the database-driven configuration system:
  * validating keys, categories, value types and color values,
  * building the grouped public payload,
  * computing a content-derived version,
  * Redis caching (fail-open) + cache invalidation on mutation,
  * audit logging of every mutation.
"""

import hashlib
import json
import logging
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ConflictError, NotFoundError, ValidationAppError
from app.config.settings import settings
from app.db.enums import ConfigCategory, ConfigValueType
from app.db.models import AppConfig, User
from app.repositories.app_config_repo import AppConfigRepository
from app.schemas.app_config import AppConfigAdminResponse, PublicAppConfigResponse
from app.security.redis import get_redis
from app.services.app_config_keys import CATEGORY_GROUP, COLOR_KEYS, public_name_for
from app.services.audit_service import AuditService

logger = logging.getLogger("app.app_config")

_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$")
_HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def validate_value_type(value: Any, value_type: ConfigValueType) -> None:
    """Ensure ``value`` is compatible with the declared ``value_type``."""
    valid = False
    if value_type == ConfigValueType.STRING:
        valid = isinstance(value, str)
    elif value_type == ConfigValueType.INTEGER:
        valid = isinstance(value, int) and not isinstance(value, bool)
    elif value_type == ConfigValueType.FLOAT:
        valid = isinstance(value, (int, float)) and not isinstance(value, bool)
    elif value_type == ConfigValueType.BOOLEAN:
        valid = isinstance(value, bool)
    elif value_type == ConfigValueType.JSON:
        valid = isinstance(value, (dict, list))
    if not valid:
        raise ValidationAppError(
            f"Value does not match value_type {value_type.value}",
            code="INVALID_CONFIG_VALUE",
        )


def validate_key_format(key: str) -> str:
    if not isinstance(key, str) or not _KEY_RE.match(key):
        raise ValidationAppError(
            "Key must match 'category.name' with lowercase letters, digits and underscores",
            code="INVALID_CONFIG_KEY",
        )
    return key


def validate_category(category: str) -> ConfigCategory:
    try:
        return ConfigCategory(category)
    except ValueError as exc:
        raise ValidationAppError(
            f"Invalid category. Allowed: {[c.value for c in ConfigCategory]}",
            code="INVALID_CONFIG_CATEGORY",
        ) from exc


def validate_color_value(key: str, value: Any) -> None:
    if key in COLOR_KEYS and isinstance(value, str) and not _HEX_COLOR_RE.match(value):
        raise ValidationAppError(
            f"Invalid color value for '{key}': expected hex like #7C3AED or #FFF",
            code="INVALID_COLOR",
        )


class AppConfigService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AppConfigRepository(session)
        self.audit = AuditService(session)

    # ------------------------------------------------------------------ public

    async def get_public(self) -> tuple[dict[str, Any], str]:
        """Return the grouped public config payload and its version.

        Reads from Redis first (fail-open); falls back to PostgreSQL when Redis
        is unavailable. Only ``is_public`` + ``is_active`` entries are included.
        """
        cached = await self._cache_get()
        if cached is not None:
            return cached["data"], cached["version"]

        rows = await self.repo.list_public_active()
        grouped = self._group(rows)
        version = self._compute_version(rows)
        await self._cache_set({"version": version, "data": grouped})
        return grouped, version

    def _group(self, rows: list[AppConfig]) -> dict[str, dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        for row in rows:
            group = CATEGORY_GROUP.get(row.category) or row.category.value.lower()
            grouped.setdefault(group, {})[public_name_for(row.key)] = row.value
        return grouped

    def _compute_version(self, rows: list[AppConfig]) -> str:
        payload = {row.key: row.value for row in rows}
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

    async def build_public_response(self) -> PublicAppConfigResponse:
        grouped, version = await self.get_public()
        return PublicAppConfigResponse(**grouped)

    # ------------------------------------------------------------------ admin

    async def list_admin(
        self,
        *,
        category: ConfigCategory | None = None,
        is_public: bool | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AppConfig]:
        return await self.repo.list_configs(
            category=category,
            is_public=is_public,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )

    async def get_by_key(self, key: str) -> AppConfig:
        obj = await self.repo.get_by_key(key)
        if obj is None:
            raise NotFoundError("Configuration key not found", code="CONFIG_KEY_NOT_FOUND")
        return obj

    async def create(self, actor: User, data: dict[str, Any]) -> AppConfig:
        key = validate_key_format(data.get("key", ""))
        if await self.repo.get_by_key(key):
            raise ConflictError("Configuration key already exists", code="CONFIG_KEY_EXISTS")

        value_type = ConfigValueType(data.get("value_type") or ConfigValueType.STRING.value)
        category = validate_category(data.get("category") or ConfigCategory.APP.value)
        value = data.get("value")
        validate_value_type(value, value_type)
        validate_color_value(key, value)

        is_public = bool(data.get("is_public", True))
        is_active = bool(data.get("is_active", True))

        obj = await self.repo.create_config(
            key=key,
            value=value,
            value_type=value_type.value,
            category=category.value,
            is_public=is_public,
            is_active=is_active,
            description=data.get("description"),
            updated_by=actor.id,
        )
        await self.audit.record(
            action="app_config.created",
            actor_user_id=actor.id,
            entity_type="app_config",
            entity_id=key,
            metadata={"key": key, "category": category.value, "value_type": value_type.value, "is_public": is_public},
        )
        await self._invalidate_cache()
        return obj

    async def update(self, actor: User, key: str, data: dict[str, Any]) -> AppConfig:
        obj = await self.get_by_key(key)

        value_type = obj.value_type if isinstance(obj.value_type, ConfigValueType) else ConfigValueType(obj.value_type)

        if "value" in data:
            value = data["value"]
            validate_value_type(value, value_type)
            validate_color_value(key, value)
            obj.value = value

        if "category" in data and data["category"] is not None:
            obj.category = validate_category(data["category"])

        if "is_public" in data and data["is_public"] is not None:
            obj.is_public = bool(data["is_public"])
        if "is_active" in data and data["is_active"] is not None:
            obj.is_active = bool(data["is_active"])
        if "description" in data:
            obj.description = data.get("description")

        obj.updated_by = actor.id
        await self.audit.record(
            action="app_config.updated",
            actor_user_id=actor.id,
            entity_type="app_config",
            entity_id=key,
            metadata={"key": key},
        )
        await self._invalidate_cache()
        return obj

    async def deactivate(self, actor: User, key: str) -> AppConfig:
        obj = await self.get_by_key(key)
        obj.is_active = False
        obj.updated_by = actor.id
        await self.audit.record(
            action="app_config.deactivated",
            actor_user_id=actor.id,
            entity_type="app_config",
            entity_id=key,
            metadata={"key": key},
        )
        await self._invalidate_cache()
        return obj

    # ------------------------------------------------------------------ cache

    async def _cache_get(self) -> dict[str, Any] | None:
        try:
            redis = await get_redis()
            raw = await redis.get(settings.APP_CONFIG_CACHE_KEY)
            if raw:
                return json.loads(raw)
        except Exception:
            logger.warning("Redis unavailable while reading app config cache", exc_info=True)
        return None

    async def _cache_set(self, payload: dict[str, Any]) -> None:
        try:
            redis = await get_redis()
            await redis.setex(settings.APP_CONFIG_CACHE_KEY, settings.APP_CONFIG_CACHE_TTL, json.dumps(payload))
        except Exception:
            logger.warning("Redis unavailable while caching app config", exc_info=True)

    async def _invalidate_cache(self) -> None:
        try:
            redis = await get_redis()
            await redis.delete(settings.APP_CONFIG_CACHE_KEY)
        except Exception:
            logger.warning("Redis unavailable while invalidating app config cache", exc_info=True)


def admin_response(obj: AppConfig) -> AppConfigAdminResponse:
    return AppConfigAdminResponse(
        id=str(obj.id),
        key=obj.key,
        value=obj.value,
        value_type=obj.value_type.value if isinstance(obj.value_type, ConfigValueType) else obj.value_type,
        category=obj.category.value if isinstance(obj.category, ConfigCategory) else obj.category,
        is_public=obj.is_public,
        is_active=obj.is_active,
        description=obj.description,
        updated_by=str(obj.updated_by) if obj.updated_by else None,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )
