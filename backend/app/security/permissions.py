"""Permission registry for the admin dashboard.

Central source of truth for the ``Role -> Permissions`` model. The backend
enforces these permissions via ``require_permission`` in ``app/api/deps.py``.
The admin frontend only uses them to decide what to render — it never enforces
authorization itself.

The default mapping below is seeded into the ``role_permissions`` table so it
can be overridden at runtime by a SUPER_ADMIN. ``permissions_for_role`` reads
the database and falls back to this registry when no rows exist yet (e.g. a
fresh test database).
"""

from app.db.enums import UserRole

# --- individual permissions ------------------------------------------------

USERS_READ = "users.read"
USERS_UPDATE = "users.update"
USERS_SUSPEND = "users.suspend"
USERS_BAN = "users.ban"
USERS_DELETE = "users.delete"

PROFILES_READ = "profiles.read"
PROFILES_MODERATE = "profiles.moderate"
PHOTOS_MODERATE = "photos.moderate"

VERIFICATION_READ = "verification.read"
VERIFICATION_APPROVE = "verification.approve"
VERIFICATION_REJECT = "verification.reject"

JOB_VERIFICATION_READ = "job_verification.read"
JOB_VERIFICATION_APPROVE = "job_verification.approve"
JOB_VERIFICATION_REJECT = "job_verification.reject"

REPORTS_READ = "reports.read"
REPORTS_RESOLVE = "reports.resolve"

MESSAGES_READ_PRIVATE = "messages.read_private"

PAYMENTS_READ = "payments.read"
PAYMENTS_REFUND = "payments.refund"

SUBSCRIPTIONS_READ = "subscriptions.read"
SUBSCRIPTIONS_MANAGE = "subscriptions.manage"

NOTIFICATIONS_SEND = "notifications.send"

APP_CONFIG_READ = "app_config.read"
APP_CONFIG_UPDATE = "app_config.update"

ANALYTICS_READ = "analytics.read"

AUDIT_LOGS_READ = "audit_logs.read"

ADMIN_USERS_READ = "admin_users.read"
ADMIN_USERS_MANAGE = "admin_users.manage"

ALL_PERMISSIONS: frozenset[str] = frozenset(
    {
        USERS_READ,
        USERS_UPDATE,
        USERS_SUSPEND,
        USERS_BAN,
        USERS_DELETE,
        PROFILES_READ,
        PROFILES_MODERATE,
        PHOTOS_MODERATE,
        VERIFICATION_READ,
        VERIFICATION_APPROVE,
        VERIFICATION_REJECT,
        JOB_VERIFICATION_READ,
        JOB_VERIFICATION_APPROVE,
        JOB_VERIFICATION_REJECT,
        REPORTS_READ,
        REPORTS_RESOLVE,
        MESSAGES_READ_PRIVATE,
        PAYMENTS_READ,
        PAYMENTS_REFUND,
        SUBSCRIPTIONS_READ,
        SUBSCRIPTIONS_MANAGE,
        NOTIFICATIONS_SEND,
        APP_CONFIG_READ,
        APP_CONFIG_UPDATE,
        ANALYTICS_READ,
        AUDIT_LOGS_READ,
        ADMIN_USERS_READ,
        ADMIN_USERS_MANAGE,
    }
)

# --- default role -> permission mapping ------------------------------------

ROLE_PERMISSIONS: dict[UserRole, set[str]] = {
    UserRole.SUPER_ADMIN: set(ALL_PERMISSIONS),
    UserRole.ADMIN: set(ALL_PERMISSIONS),
    UserRole.MODERATOR: {
        USERS_READ,
        USERS_UPDATE,
        USERS_SUSPEND,
        USERS_BAN,
        PROFILES_READ,
        PROFILES_MODERATE,
        PHOTOS_MODERATE,
        VERIFICATION_READ,
        JOB_VERIFICATION_READ,
        REPORTS_READ,
        REPORTS_RESOLVE,
        MESSAGES_READ_PRIVATE,
    },
    UserRole.VERIFIER: {
        PROFILES_READ,
        PHOTOS_MODERATE,
        VERIFICATION_READ,
        VERIFICATION_APPROVE,
        VERIFICATION_REJECT,
        JOB_VERIFICATION_READ,
        JOB_VERIFICATION_APPROVE,
        JOB_VERIFICATION_REJECT,
    },
    UserRole.SUPPORT: {
        USERS_READ,
        USERS_UPDATE,
        PROFILES_READ,
        REPORTS_READ,
        REPORTS_RESOLVE,
        MESSAGES_READ_PRIVATE,
        NOTIFICATIONS_SEND,
    },
    UserRole.FINANCE: {
        PAYMENTS_READ,
        PAYMENTS_REFUND,
        SUBSCRIPTIONS_READ,
        SUBSCRIPTIONS_MANAGE,
        ANALYTICS_READ,
    },
    UserRole.ANALYST: {
        USERS_READ,
        PAYMENTS_READ,
        SUBSCRIPTIONS_READ,
        ANALYTICS_READ,
        AUDIT_LOGS_READ,
    },
    UserRole.USER: set(),
}


def permissions_for_role_default(role: UserRole) -> set[str]:
    return set(ROLE_PERMISSIONS.get(role, set()))
