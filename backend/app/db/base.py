import uuid
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

from sqlalchemy import DateTime, MetaData
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON, TypeDecorator

EnumT = TypeVar("EnumT", bound=Enum)

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

DEFAULT_META = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    metadata = DEFAULT_META


class GUID(TypeDecorator[uuid.UUID]):
    """UUID primary key type that maps to native UUID on Postgres and CHAR(36) elsewhere."""

    impl = PG_UUID
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(PG_UUID(as_uuid=True))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class UTCDateTime(TypeDecorator[datetime]):
    """Timezone-aware datetime on Postgres; naive-tolerant on SQLite."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(DateTime(timezone=True))


class JSONBType(TypeDecorator):
    """JSONB on Postgres, JSON elsewhere (keeps SQLite tests working)."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB(none_as_null=True))
        return dialect.type_descriptor(JSON())


def gen_uuid() -> uuid.UUID:
    return uuid.uuid4()


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True, index=True)


def enum_column(
    enum_cls: type[EnumT],
    *,
    nullable: bool = False,
    default: object | None = None,
    index: bool = False,
    server_default: Any = None,
) -> Mapped[EnumT]:
    """SQLAlchemy Enum stored as VARCHAR + CHECK constraint (portable to SQLite tests)."""
    return mapped_column(
        SAEnum(enum_cls, native_enum=False, values_callable=lambda e: [m.value for m in e], length=32),
        nullable=nullable,
        default=default,
        server_default=server_default,
        index=index,
    )


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(  # noqa: A003
        GUID, primary_key=True, default=gen_uuid
    )
