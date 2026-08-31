"""extend app_config for remote config

Revision ID: 2f5a9c32816d
Revises: ed1fc2a55f8d
Create Date: 2026-08-09 15:44:13.370422

Extends ``app_config`` with value typing, categories, visibility/activity flags,
an admin ``updated_by`` reference and timestamps for the remote configuration
system. Uses ``batch_alter_table`` so SQLite recreates the table while Postgres
uses native ALTERs. Server defaults backfill existing rows and are then dropped
so the schema matches the models exactly (Python-side defaults handle inserts).
"""

import sqlalchemy as sa
from alembic import op

revision = "2f5a9c32816d"
down_revision = "ed1fc2a55f8d"
branch_labels = None
depends_on = None

_value_type_enum = sa.Enum(
    "STRING",
    "INTEGER",
    "FLOAT",
    "BOOLEAN",
    "JSON",
    name="configvaluetype",
    native_enum=False,
    length=32,
)
_category_enum = sa.Enum(
    "BRANDING",
    "APP",
    "FEATURES",
    "LIMITS",
    "PRICING",
    "VERSIONS",
    "LEGAL",
    "SUPPORT",
    name="configcategory",
    native_enum=False,
    length=32,
)


def upgrade() -> None:
    with op.batch_alter_table("app_config") as batch_op:
        # Backfill-safe column additions (server defaults populate existing rows).
        batch_op.add_column(sa.Column("value_type", _value_type_enum, nullable=False, server_default="STRING"))
        batch_op.add_column(sa.Column("category", _category_enum, nullable=False, server_default="APP"))
        batch_op.add_column(sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column("updated_by", sa.Uuid(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )
        )

        batch_op.alter_column(
            "key", existing_type=sa.String(length=100), type_=sa.String(length=120), existing_nullable=False
        )

        batch_op.create_index(op.f("ix_app_config_category"), ["category"], unique=False)
        batch_op.create_index(op.f("ix_app_config_is_active"), ["is_active"], unique=False)
        batch_op.create_index(op.f("ix_app_config_is_public"), ["is_public"], unique=False)
        batch_op.create_foreign_key(
            op.f("fk_app_config_updated_by_users"),
            "users",
            ["updated_by"],
            ["id"],
            ondelete="SET NULL",
        )

        # Drop the backfill defaults so the schema matches the models (zero drift).
        batch_op.alter_column(
            "value_type", existing_type=_value_type_enum, server_default=None, existing_server_default="STRING"
        )
        batch_op.alter_column(
            "category", existing_type=_category_enum, server_default=None, existing_server_default="APP"
        )
        batch_op.alter_column(
            "is_public", existing_type=sa.Boolean(), server_default=None, existing_server_default=sa.true()
        )
        batch_op.alter_column(
            "is_active", existing_type=sa.Boolean(), server_default=None, existing_server_default=sa.true()
        )
        batch_op.alter_column(
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            server_default=None,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        batch_op.alter_column(
            "updated_at",
            existing_type=sa.DateTime(timezone=True),
            server_default=None,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),
        )


def downgrade() -> None:
    with op.batch_alter_table("app_config") as batch_op:
        batch_op.drop_constraint(op.f("fk_app_config_updated_by_users"), type_="foreignkey")
        batch_op.drop_index(op.f("ix_app_config_is_public"))
        batch_op.drop_index(op.f("ix_app_config_is_active"))
        batch_op.drop_index(op.f("ix_app_config_category"))
        batch_op.alter_column(
            "key", existing_type=sa.String(length=120), type_=sa.String(length=100), existing_nullable=False
        )
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")
        batch_op.drop_column("updated_by")
        batch_op.drop_column("is_active")
        batch_op.drop_column("is_public")
        batch_op.drop_column("category")
        batch_op.drop_column("value_type")
