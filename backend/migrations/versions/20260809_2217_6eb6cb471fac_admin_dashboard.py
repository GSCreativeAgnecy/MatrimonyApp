"""admin dashboard: rbac, totp, campaigns, moderation fields

Revision ID: 6eb6cb471fac
Revises: 2f5a9c32816d
Create Date: 2026-08-09 22:17:00.000000

Adds the admin-dashboard backend support:

- ``role_permissions``  : Role -> Permission table for the RBAC model.
- ``user_totp_secrets`` : opt-in TOTP two-factor secrets.
- ``totp_recovery_codes``: single-use recovery codes (hashed).
- ``notification_campaigns``: admin broadcast campaigns processed by ARQ.
- Extends ``users.role`` CHECK to the new SUPPORT/FINANCE/ANALYST roles.
- Adds profile-review moderation columns to ``profiles``.
- Adds ``job_verifications.reviewer_notes``.

``batch_alter_table`` keeps SQLite and Postgres happy. Server defaults backfill
existing rows and are then dropped so the schema matches the models exactly.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "6eb6cb471fac"
down_revision = "2f5a9c32816d"
branch_labels = None
depends_on = None

_role_enum = sa.Enum(
    "USER",
    "MODERATOR",
    "VERIFIER",
    "SUPPORT",
    "FINANCE",
    "ANALYST",
    "ADMIN",
    "SUPER_ADMIN",
    name="userrole",
    native_enum=False,
    length=32,
)
_review_status_enum = sa.Enum(
    "PENDING",
    "APPROVED",
    "REJECTED",
    "REQUEST_CHANGES",
    "SUSPENDED",
    name="profilereviewstatus",
    native_enum=False,
    length=32,
)
_channel_enum = sa.Enum(
    "PUSH",
    "EMAIL",
    "SMS",
    name="notificationchannel",
    native_enum=False,
    length=32,
)
_campaign_status_enum = sa.Enum(
    "QUEUED",
    "SENDING",
    "DONE",
    "FAILED",
    "CANCELLED",
    name="notificationcampaignstatus",
    native_enum=False,
    length=32,
)


def _recreate_user_role_check(*, allow_new_roles: bool) -> None:
    """Recreate the ``users.role`` CHECK constraint.

    The initial migration created it as a plain ``userrole`` CHECK (the enum
    name) on Postgres. Alembic batch mode would rename it to ``ck_users_userrole``
    (naming convention) and fail with ``constraint does not exist``, so use raw
    SQL on Postgres. SQLite never renders an enum CHECK constraint, so there is
    nothing to migrate there.
    """
    allowed = (
        "('USER','MODERATOR','VERIFIER','SUPPORT','FINANCE','ANALYST','ADMIN','SUPER_ADMIN')"
        if allow_new_roles
        else "('USER','MODERATOR','VERIFIER','ADMIN','SUPER_ADMIN')"
    )
    if op.get_bind().dialect.name == "postgresql":
        # Drop by either possible name, then recreate explicitly.
        op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS userrole")
        op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_userrole")
        op.execute(f"ALTER TABLE users ADD CONSTRAINT userrole CHECK (role IN {allowed})")


def upgrade() -> None:
    # --- users.role: allow the new admin roles -------------------------------
    _recreate_user_role_check(allow_new_roles=True)

    # --- role_permissions ----------------------------------------------------
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("permission", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_role_permissions")),
        sa.UniqueConstraint("role", "permission", name="uq_role_permission"),
    )
    op.create_index(op.f("ix_role_permissions_permission"), "role_permissions", ["permission"], unique=False)
    op.create_index(op.f("ix_role_permissions_role"), "role_permissions", ["role"], unique=False)

    # --- user_totp_secrets ---------------------------------------------------
    op.create_table(
        "user_totp_secrets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("secret", sa.String(length=64), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_user_totp_secrets_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_totp_secrets")),
        sa.UniqueConstraint("user_id", name=op.f("uq_user_totp_secrets_user_id")),
    )
    op.create_index(op.f("ix_user_totp_secrets_user_id"), "user_totp_secrets", ["user_id"], unique=False)

    # --- totp_recovery_codes -------------------------------------------------
    op.create_table(
        "totp_recovery_codes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("code_hash", sa.String(length=128), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_totp_recovery_codes_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_totp_recovery_codes")),
    )
    op.create_index(op.f("ix_totp_recovery_codes_user_id"), "totp_recovery_codes", ["user_id"], unique=False)

    # --- notification_campaigns ----------------------------------------------
    op.create_table(
        "notification_campaigns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.String(length=2000), nullable=False),
        sa.Column("channel", _channel_enum, nullable=False),
        sa.Column("audience", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("status", _campaign_status_enum, nullable=False),
        sa.Column("target_count", sa.Integer(), nullable=True),
        sa.Column("delivered_count", sa.Integer(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f("fk_notification_campaigns_created_by_users"), ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notification_campaigns")),
    )
    op.create_index(
        op.f("ix_notification_campaigns_created_at"), "notification_campaigns", ["created_at"], unique=False
    )
    op.create_index(op.f("ix_notification_campaigns_status"), "notification_campaigns", ["status"], unique=False)
    op.create_index(op.f("ix_notification_campaigns_channel"), "notification_campaigns", ["channel"], unique=False)

    # --- profiles: moderation columns -----------------------------------------
    with op.batch_alter_table("profiles") as batch_op:
        batch_op.add_column(sa.Column("review_status", _review_status_enum, nullable=False, server_default="PENDING"))
        batch_op.add_column(sa.Column("reviewed_by", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("review_reason", sa.String(length=1000), nullable=True))
        batch_op.create_foreign_key(
            op.f("fk_profiles_reviewed_by_users"), "users", ["reviewed_by"], ["id"], ondelete="SET NULL"
        )
        batch_op.create_index(op.f("ix_profiles_review_status"), ["review_status"], unique=False)
        batch_op.alter_column(
            "review_status", existing_type=_review_status_enum, server_default=None, existing_server_default="PENDING"
        )

    # --- job_verifications: reviewer notes ------------------------------------
    with op.batch_alter_table("job_verifications") as batch_op:
        batch_op.add_column(sa.Column("reviewer_notes", sa.String(length=1000), nullable=True))

    # --- users: suspension ledger ----------------------------------------------
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("suspended_until", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("suspended_reason", sa.String(length=1000), nullable=True))
        batch_op.add_column(sa.Column("suspended_by", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            op.f("fk_users_suspended_by_users"), "users", ["suspended_by"], ["id"], ondelete="SET NULL"
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint(op.f("fk_users_suspended_by_users"), type_="foreignkey")
        batch_op.drop_column("suspended_by")
        batch_op.drop_column("suspended_reason")
        batch_op.drop_column("suspended_until")
        batch_op.drop_column("suspended_at")

    with op.batch_alter_table("job_verifications") as batch_op:
        batch_op.drop_column("reviewer_notes")

    with op.batch_alter_table("profiles") as batch_op:
        batch_op.drop_index(op.f("ix_profiles_review_status"))
        batch_op.drop_constraint(op.f("fk_profiles_reviewed_by_users"), type_="foreignkey")
        batch_op.drop_column("review_reason")
        batch_op.drop_column("reviewed_at")
        batch_op.drop_column("reviewed_by")
        batch_op.drop_column("review_status")

    op.drop_index(op.f("ix_notification_campaigns_channel"), table_name="notification_campaigns")
    op.drop_index(op.f("ix_notification_campaigns_status"), table_name="notification_campaigns")
    op.drop_index(op.f("ix_notification_campaigns_created_at"), table_name="notification_campaigns")
    op.drop_table("notification_campaigns")

    op.drop_index(op.f("ix_totp_recovery_codes_user_id"), table_name="totp_recovery_codes")
    op.drop_table("totp_recovery_codes")

    op.drop_index(op.f("ix_user_totp_secrets_user_id"), table_name="user_totp_secrets")
    op.drop_table("user_totp_secrets")

    op.drop_index(op.f("ix_role_permissions_role"), table_name="role_permissions")
    op.drop_index(op.f("ix_role_permissions_permission"), table_name="role_permissions")
    op.drop_table("role_permissions")

    _recreate_user_role_check(allow_new_roles=False)

