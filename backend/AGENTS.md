# AGENTS.md

Guidance for AI agents and developers working on the **Matchmaking API** — a production-ready matrimony / matchmaking backend.

Read this file before modifying anything. It encodes the architecture, conventions, invariants, and the "gotchas" that are easy to reintroduce.

---

## 1. What this project is

- FastAPI + Pydantic v2 REST backend consumed primarily by a React Native mobile app.
- Async everywhere: `SQLAlchemy 2.0` (async) + `asyncpg` + Alembic, `redis.asyncio`, `arq` workers.
- PostgreSQL, UUID PKs, `JSONB`, `timestamptz`.
- Target scale: hundreds of thousands to millions of users without an architectural rewrite.

**Golden rule:** the API layer contains no business logic; the service layer is the only place business rules live; repositories encapsulate query construction; Pydantic schemas are the only objects crossing the HTTP boundary (never raw ORM models).

---

## 2. Repo layout

```text
app/
├── main.py                  # FastAPI app, CORS, error handlers, /static mount, /health
├── config/
│   ├── settings.py          # pydantic-settings (cached via get_settings())
│   └── logging.py           # logging config + setup_logging()
├── db/
│   ├── base.py              # Base, GUID, UTCDateTime, JSONBType, enum_column, mixins
│   ├── enums.py             # ALL domain enums (StrEnum)
│   ├── session.py           # engine + async_sessionmaker (build_engine), get_session
│   └── models/              # one module per domain; __init__.py re-exports all
├── api/
│   ├── deps.py              # get_session, get_current_user, require_role, require_permission, rate_limit, get_storage
│   ├── errors.py            # AppError hierarchy + error handlers + envelope helpers
│   └── v1/                  # one router module per resource; __init__.py aggregates (admin_* = dashboard routers)
├── schemas/                 # Pydantic request/response models (one module per domain)
│   ├── app_config.py        # admin + public grouped app-config schemas
│   └── admin.py             # admin dashboard request/response schemas
├── repositories/            # data access; BaseRepository[T] + domain repos
│   └── app_config_repo.py   # AppConfig queries (repo method is `list_configs`, not `list`)
├── services/                # business logic; service classes take AsyncSession
│   ├── storage.py           # StorageBackend protocol + Local/S3 impls
│   ├── astrology_provider.py# AstrologyProvider protocol + no-op impl
│   ├── app_config_service.py# remote app configuration service (validation, cache, version)
│   ├── app_config_keys.py   # central registry of known config keys + defaults
│   ├── permission_service.py# Role -> Permission resolution (DB rows, static fallback)
│   ├── totp_service.py      # TOTP 2FA (pyotp) + hashed recovery codes
│   ├── admin_analytics_service.py  # dashboard/analytics aggregates (never raw scans)
│   ├── admin_user_service.py       # admin user actions + sub-resource reads
│   ├── notification_campaign_service.py  # campaign validation + batched fan-out
│   └── ...
├── workers/                 # ARQ: arq_app.py (settings), tasks.py, enqueue.py
├── security/                # jwt.py, password.py (argon2), redis.py, rate_limit.py, permissions.py (RBAC registry)
├── seed.py                  # idempotent seed script (python -m app.seed)
├── utils/                   # currently empty; add cross-cutting helpers here
admin/                       # Admin web dashboard (Next.js, separate deployable app)
migrations/                  # Alembic (async env.py), versions/
tests/                       # pytest suite (SQLite in-memory, no Postgres/Redis)
docs/architecture.md         # full design doc: ERD, enums, indexes, endpoints, designs
docs/admin-dashboard.md      # admin dashboard architecture, setup, permissions, deployment
```

---

## 3. Commands (always run these before and after changes)

```bash
# Install (Windows)
.venv\Scripts\activate
pip install -e ".[dev]"

# Tests (SQLite in-memory; NO Postgres or Redis needed)
pytest                                   # full suite
pytest tests/test_auth.py -q             # single file
pytest tests/test_swipes_matches.py::TestSwipes::test_like -q

# Lint + format
ruff check app migrations tests
ruff format app migrations tests

# Type check (only app/ — tests & migrations are excluded)
mypy app

# Migrations (needs DATABASE_URL to a real DB)
alembic upgrade head
alembic downgrade -1
alembic revision --autogenerate -m "describe change"
alembic check                     # drift check — run against Postgres, NOT SQLite

# Seed (idempotent)
python -m app.seed

# Run API / worker
uvicorn app.main:app --reload
arq app.workers.arq_app.WorkerSettings

# Docker (everything: api, worker, postgres, redis, migrate+seed)
docker compose up --build
```

**CI definition of done:** `pytest` green, `ruff check` clean, `mypy app` clean.

---

## 4. Architecture & layering rules

| Layer | Responsibility | Must not do |
| --- | --- | --- |
| `api/v1/*.py` routers | HTTP glue: parse request, call service, commit, return `ApiResponse[...]` | No business logic, no direct query building |
| `schemas/*` | Request/response models | No DB access |
| `services/*` | Business rules, orchestration, authorization checks | No HTTP/Request access (pass data in), must not leak raw ORM to response |
| `repositories/*` | Query construction, entity persistence | No business rules |
| `db/models/*` | Column/constraint/relationship declarations | No business logic, no methods that implement rules |
| `workers/*` | Background jobs, enqueueing | Never in request hot path |

- **Routers must commit the session** after calling services (services flush; routers commit).
- **Never** call `Base.metadata.create_all` for production schema — use Alembic. `init_models()` in `db/session.py` exists only for local convenience/tests.
- **No circular imports.** Models import only `app.db.base`, `app.db.enums`, and other model modules via string relationships. Services import services/repositories, never routers.
- **No global mutable state.** The only module-level singletons are lazy caches: Redis client (`app.security.redis._redis`) and storage (`build_storage()`), both created on first use.
- **Import rule for `get_session`:** every router uses `Depends(get_session)` where `get_session` is imported from **`app.api.deps`** — never from `app.db.session`. The test suite overrides `app.dependency_overrides[get_session]`; importing the wrong symbol silently disables the override.

---

## 5. Configuration (settings & env)

- `app/config/settings.py` is a `pydantic-settings` `BaseSettings`; read env vars (optionally from `.env`). Access via `from app.config.settings import settings` (a cached singleton) or `get_settings()`.
- Never hardcode secrets, URLs, or pricing. `.env` is git-ignored; document new vars in `.env.example`.
- Key settings and what they control:

| Setting | Purpose |
| --- | --- |
| `DATABASE_URL` | Async Postgres URL (`postgresql+asyncpg://...`) |
| `TEST_DATABASE_URL` | Test DB (SQLite by default) |
| `REDIS_URL` | Rate limiting, OTP/reset/verify state, denylist, recommendation cache |
| `JWT_SECRET_KEY`, `JWT_ALGORITHM` | JWT signing (HS256). Rotate in prod. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` | Token lifetimes |
| `STORAGE_BACKEND` | `local` (dev) or `s3` |
| `S3_*` | S3-compatible storage endpoint/bucket/keys/region/expiry |
| `LOCAL_STORAGE_PATH` | Filesystem root for `local` backend |
| `PAYMENT_PROVIDER` | `mock` (dev) or `stripe` |
| `PAYMENT_API_KEY`, `PAYMENT_WEBHOOK_SECRET` | Provider keys / webhook verification |
| `SMTP_*`, `SMS_PROVIDER` | Email/SMS delivery |
| `RATE_LIMIT_ENABLED`, `LOGIN_RATE_LIMIT`, `OTP_RATE_LIMIT` | Rate limiting (e.g. `10/15m`) |
| `CORS_ORIGINS` | Allowed origins (JSON list) |
| `APP_CONFIG_CACHE_TTL`, `APP_CONFIG_CACHE_KEY` | Public app-config Redis cache (TTL seconds, key name) |
| `LOCAL_JOB_VERIFICATION_PRICE`, `NRI_JOB_VERIFICATION_PRICE` | Fallback verification pricing (DB `app_config` takes precedence) |

---

## 6. Database & model conventions

### UUID + PK
```python
id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
```
- Always pass `default=gen_uuid` (from `app.db.base`). Forgetting it ⇒ `NOT NULL constraint failed` on insert.
- `GUID` (a `TypeDecorator`) coerces `str`→`UUID` on bind and `str`→`UUID` on result — callers may pass either, but **prefer `UUID` objects** internally.

### Timestamps
```python
created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=datetime.utcnow, nullable=False)
```
- Mixins: `TimestampMixin` (created_at/updated_at), `SoftDeleteMixin` (deleted_at).
- **Timezone pitfall:** SQLite stores naive datetimes. When comparing a column read back from the DB against `datetime.now(UTC)`, normalize the naive value first (`dt.replace(tzinfo=timezone.utc)`) or you get `TypeError: can't compare offset-naive and offset-aware`.

### Enums
- Define every domain enum in `app/db/enums.py` as `StrEnum`.
- In models use `enum_column(EnumClass, default=..., index=True)` from `app.db.base`.
- Enums are stored as **VARCHAR + CHECK constraint** (`native_enum=False`) — portable between Postgres and SQLite tests. Do not switch to native PG enums.
- Read/write `EnumClass` members in code; use `.value` only for serialization. Passing raw strings into enum columns is a bug.

### JSONB
- Use `JSONBType` (from `app.db.base`) — real `JSONB` on Postgres, `JSON` on SQLite.
- **`metadata` is a reserved attribute name** in SQLAlchemy Declarative. The column is named `metadata` in DB but the mapped attribute is `meta`. Always use `payment.meta` / `audit_log.meta`.

### Naming
- Constraint names are auto-generated by the naming convention in `app.db.base.NAMING_CONVENTION` (prefixes `pk_`, `fk_`, `uq_`, `ix_`, `ck_`). Alembic autogenerate respects them.
- Multi-column indexes and composite uniques go in `__table_args__`.

### Relationships
- Prefer explicit queries (`select()`, `session.get`) over deep ORM relationship cascades. Keep relationships minimal (`Profile.user`, `Conversation.participants`, etc.).
- Foreign keys must declare explicit `ondelete` behavior.

---

## 7. Models module map

| Module | Tables |
| --- | --- |
| `user.py` | `users`, `refresh_tokens` |
| `profile.py` | `profiles`, `user_privacy_settings` |
| `photo.py` | `photos` |
| `lookups.py` | `languages`, `user_languages`, `interests`, `user_interests`, `religions`, `castes`, `countries`, `states`, `education_levels`, `occupations`, `app_config` |
| `family.py` | `families`, `family_members` |
| `astrology.py` | `astrology_profiles` |
| `preference.py` | `partner_preferences`, `preferred_religions`, `preferred_castes`, `preferred_languages`, `preferred_countries`, `preferred_states`, `preferred_diets` (all junction tables share `PreferredJunctionBase`) |
| `swipe.py` | `swipes` |
| `match.py` | `matches` |
| `message.py` | `conversations`, `conversation_participants`, `messages` |
| `moderation.py` | `blocks`, `reports` |
| `notification.py` | `notifications` |
| `billing.py` | `subscription_plans`, `subscriptions`, `payments` |
| `verification.py` | `job_verifications` |
| `share.py` | `profile_shares` |
| `audit.py` | `audit_logs` |

---

## 8. Code patterns (copy these skeletons)

### Router (e.g. `app/api/v1/myresource.py`)
```python
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.db.models import User
from app.schemas.common import ApiResponse
from app.services.my_service import MyService

router = APIRouter(prefix="/my-resource", tags=["my-resource"])


@router.get("", response_model=ApiResponse[list[MyItemResponse]])
async def list_items(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[list[MyItemResponse]]:
    items = await MyService(session).list_for_user(user.id)
    return ApiResponse(data=[MyItemResponse.model_validate(i) for i in items])
```

Rules for routers:
- `response_model` is always `ApiResponse[...]`; return `ApiResponse(data=...)`.
- Import `get_session` from `app.api.deps`.
- Call one service method, then `await session.commit()` for mutations, then build the response.
- Never build raw SQL, never implement business rules, never leak ORM objects.

### Service
```python
class MyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = MyRepository(session)
        self.audit = AuditService(session)

    async def do_thing(self, user: User, target_id: UUID) -> Model:
        # authorization check first
        obj = await self.repo.get_for_user(target_id, user.id)
        if obj is None:
            raise NotFoundError("...", code="...")
        # business rule ...
        await self.audit.record(action="my.action", actor_user_id=user.id, entity_type="...", entity_id=str(obj.id))
        return obj
```

### Repository
```python
class MyRepository(BaseRepository[MyModel]):
    model = MyModel

    async def get_for_user(self, id: UUID, user_id: UUID) -> MyModel | None:
        from sqlalchemy import select
        return await self.session.scalar(select(MyModel).where(MyModel.id == id, MyModel.user_id == user_id))
```
- Only create a repository when queries are non-trivial or reused; simple `session.get`/`session.scalar` can live in services.

---

## 9. Auth & security invariants (do not break these)

- **Passwords:** Argon2id via `app.security.password.hash_password/verify_password`. Never log or store plaintext.
- **JWT:** HS256, secret from `settings.JWT_SECRET_KEY`. Access token ~15 min; refresh token ~30 days.
- **Refresh rotation:** every `/auth/refresh` revokes the presented token (`refresh_tokens.revoked_at`, `replaced_by_jti`) and issues a new pair. Reusing a rotated token must fail with `401 TOKEN_REVOKED`.
- **Never trust the client** for: `user_id`, premium status, subscription status, payment status, verification status, admin role. All derived server-side.
- **`get_current_user`** (`app/api/deps.py`) is the only way to resolve a user from a request; it rejects banned/deleted accounts.
- **`require_role(*roles)`** gates admin/verifier endpoints and raises **`403 FORBIDDEN`** (a `ForbiddenError`) for insufficient roles. Tests for admin endpoints assert 403.
- **`require_permission(*perms)` / `require_any_permission(*perms)`** gate admin-dashboard endpoints by **permission**, not role. Permissions resolve via `PermissionService.permissions_for_role` (DB `role_permissions` rows, falling back to the static `ROLE_PERMISSIONS` registry in `app/security/permissions.py`). Do not hand-roll permission checks in routers.
- **2FA (TOTP):** opt-in per user (`user_totp_secrets` + hashed `totp_recovery_codes`). When enabled, `POST /auth/login` returns `{requires_2fa, mfa_token}` and `POST /auth/totp/verify` completes the login. Do not bypass this on admin logins.
- **Ownership checks** live in services (photos, preferences, family, matches, conversations, shares). Example: `get_for_user(photo_id, user.id)`.
- **Rate limiting** (`app/api/deps.py: rate_limit("login")`) is Redis-backed and **fail-open** — a Redis outage must never lock users out. Auth/OTP flows use it.
- Redis token storage (OTP, reset, email-verify) also **fail-open** via `_redis_setex/_redis_get` in `auth_service.py`.
- Errors use the `{"error": {"code", "message"}}` envelope via `AppError` subclasses. Never leak stack traces (the global handler logs and returns a generic message).

---

## 10. Core business rules (enforced in services)

1. A user cannot swipe on themselves, blocked users, deleted users, or banned users.
2. Blocked users never appear in recommendations, search, likes, matches, or messaging.
3. Deleted/banned users never appear in discovery.
4. Private profiles must not expose restricted fields (`PublicProfileResponse` vs `MatchedProfileResponse` vs `OwnProfileResponse`).
5. A match is created **only** on mutual like (`swipe_service.swipe` checks the reverse swipe and calls `match_repo.create_between`).
6. No duplicate active matches — `(user1_id, user2_id)` is normalized to `min < max` and has a unique constraint.
7. Payment status comes **only** from verified provider webhooks (`payment_service.handle_webhook`, idempotent by `provider_payment_id`).
8. Verification status changes only via `VERIFIER`/`ADMIN` review or trusted webhook transitions.
9. Premium is **derived** from an active `Subscription` — never stored as `is_premium`.
10. Server-controlled fields (verification status, subscription, payment status, role) are not client-settable.

---

## 11. Profile response shapes (privacy contract)

Four distinct shapes — never blur them:

| Shape | Who sees it | Included |
| --- | --- | --- |
| `OwnProfileResponse` | the profile owner | everything incl. exact lat/lng, income |
| `PublicProfileResponse` | any other user (not matched) | safe fields only; NO phone/email/income/DOB/coords/workplace |
| `MatchedProfileResponse` | a matched user | public fields + phone, email, workplace |
| `AdminProfileResponse` | admin | own-profile fields + account info |

- Exact `location_lat`/`location_lng`, `annual_income`, `phone_number`, `email` must never appear in the public shape.
- Distance is returned only when the owner's `user_privacy_settings.show_distance` is true.

---

## 12. Testing conventions

- Run against **in-memory SQLite** (`sqlite+aiosqlite:///:memory:` with `poolclass=StaticPool`). No Postgres/Redis required.
- `tests/conftest.py` provides: `engine`, `session_factory`, `client` (httpx `ASGITransport`), and helpers `register_user`, `login_user`, `auth_headers`, `create_full_profile`, `unique_email`.
- Autouse fixtures: `fast_argon2` (low-cost hasher for speed) and `no_enqueue` (worker calls become no-ops).
- `settings.RATE_LIMIT_ENABLED = False` and Redis points at a closed port with short timeout so fail-open paths return fast.
- Session dependency is overridden via `app.dependency_overrides[get_session]` — all routers must import `get_session` from `app.api.deps` (never `app.db.session`) or the override silently won't apply.
- Coverage is required for: auth (register/login/refresh/expiry/authorization), profiles + privacy, swipes (like/pass/duplicate/mutual→match), matches (unmatch, blocked interaction), messaging (authorized/unauthorized access, send/read), payments (success/failed/duplicate/invalid webhook), verification (submit/approve/reject), and object-authorization.
- Tests are isolated per function (fresh in-memory DB each test).

---

## 13. Pydantic / response conventions

- **Response envelope:** always `ApiResponse[T]` → `{"data": ..., "meta": {...}}`. Errors → `{"error": {...}}`.
- Response schemas that use `model_config = ConfigDict(from_attributes=True)` and map `id`/`*_id` UUID columns must type those fields as **`UUID`** (not `str`). Pydantic v2 does NOT coerce `UUID → str`.
- Schemas built manually (from dicts) can use `str` fields since the router passes `str(...)`.
- Requests use `use_enum_values=True` where appropriate; validate ranges in the schema with `Field(ge=..., le=...)` and `model_validator`.

---

## 14. Recommendations architecture

```
Candidate Generation -> Hard Filters -> Scoring -> Ranking -> Feed
```

- `app/services/recommendation_service.py`:
  - `_candidates()`: active profiles, excluding self / blocked (both directions) / swiped / matched.
  - `_preferences()`: REQUIRED items → hard filters; PREFERRED items → soft scoring.
  - `DeterministicScoringEngine` implements the `ScoringEngine` protocol.
- Scoring keys in `WEIGHTS` (they are the **only** legal keys — do not add a new factor without adding a weight and a reason code):
  `age, height, location, religion, caste, language, education, occupation, diet, smoking, drinking, family, interests, marital, intent`.
- `_REASON_MAP` maps weight keys → reason codes (`AGE_MATCH`, `LOCATION_MATCH`, `SHARED_INTERESTS`, ...).
- `build_feed()` returns `{"items": [dicts], "next_cursor", "has_more"}`; the router wraps them into pydantic `RecommendationItem`. Do NOT double-wrap.
- Feed is cached in Redis (`recs:{user_id}`, TTL 900s) and is invalidated/ignored when Redis is down (fail-open).
- To swap in an ML model: implement `ScoringEngine.score()` and inject it — the pipeline is untouched.

---

## 15. Payments & verification

- `PaymentProvider` protocol in `payment_service.py` (`mock` in dev, `stripe` pluggable). `build_provider()` selects by `PAYMENT_PROVIDER`.
- Webhook endpoint: `POST /api/v1/payments/webhook/{provider}` verifies signature, then `handle_webhook` is **idempotent**:
  - resolve by `provider_payment_id` → fall back to internal payment UUID (mock/webhook-retry convenience);
  - already-terminal payments return `{"status": "duplicate"}`;
  - success → `payment.status = SUCCESS`, then downstream transition (subscription activation or job verification → `UNDER_REVIEW`) via `_mark_success`.
- Job verification pricing is DB-driven from `app_config` (`pricing.local_job_verification=119`, `pricing.nri_job_verification=199`, legacy keys + `settings` fallback). Never hardcode pricing in logic.
- Status machine: `PENDING_PAYMENT -> UNDER_REVIEW -> VERIFIED | REJECTED | EXPIRED`.

---

## 15b. Remote app configuration

- `app_config` is the backend-managed config source for the mobile app (branding, feature flags, public limits/pricing, app versions, maintenance state, legal/support). It is **not** a secret store.
- Model (in `app/db/models/lookups.py`): `key` (unique), `value` (JSONB — scalars or structured JSON), `value_type` (`ConfigValueType`), `category` (`ConfigCategory`), `is_public`, `is_active`, `description`, `updated_by`.
- **Known keys live in `app/services/app_config_keys.py`** (`CONFIG_KEY_SPECS`) — the single source for seeds and validation. Never hardcode config keys elsewhere.
- Public endpoint `GET /api/v1/app/config` is **unauthenticated** and returns only `is_public && is_active` entries, grouped by category, with a content-derived `meta.version` (SHA-256 prefix). Stable field names + `extra="allow"` schemas keep old clients working.
- Public grouping strips `enable_` prefixes (`features.enable_registration` → `features.registration`) via `app_config_keys.public_name_for()`.
- Admin endpoints `/api/v1/admin/app-config` are `ADMIN`/`SUPER_ADMIN` only (`require_role`). `key` and `value_type` are immutable after creation; `DELETE` is a soft deactivation.
- Validation (in `app_config_service.py`): key format, value↔value_type match, category membership, hex colors for `*_color` keys, duplicate key → `409 CONFIG_KEY_EXISTS`.
- Redis cache key `app_config:public` (TTL `APP_CONFIG_CACHE_TTL`) with **fail-open** behavior; every mutation invalidates the cache and writes an audit event (`app_config.created/updated/deactivated`).
- Pricing shown to clients is display-only; payment/verification services always read the authoritative server-side price and never trust a client amount.

---

## 15c. Admin dashboard, RBAC & 2FA

- The admin dashboard is a **separate Next.js app** (`admin/`), a pure API client. It never connects to PostgreSQL, never holds secrets, and never enforces authorization itself (UI hiding is convenience only).
- **RBAC:** roles are `SUPER_ADMIN, ADMIN, MODERATOR, VERIFIER, SUPPORT, FINANCE, ANALYST`. Permissions are strings (see `app/security/permissions.py` `ALL_PERMISSIONS`); defaults live in `ROLE_PERMISSIONS` and are seeded into `role_permissions`. All admin endpoints are gated with `require_permission`/`require_any_permission` — never hand-roll role checks. `SUPER_ADMIN` permissions are immutable.
- **Admin API:** `/api/v1/admin/*` routers in `app/api/v1/admin_*.py` (dashboard, users, moderation, matches, messages, payments, subscriptions, verification, notifications, analytics, audit, admin-users). Routers commit; services hold rules; aggregates never scan raw tables.
- **Audit everything sensitive:** suspension, ban, delete, moderation, verification, refunds, plan changes, app-config changes, role/permission changes, admin create/disable, private-message access (`admin.message_view`), notification campaigns. Pass `ip_address`/`user_agent` from `get_request_context(request)`.
- **2FA:** `TotpService` (pyotp). `user_totp_secrets` stores the base32 secret; `totp_recovery_codes` stores SHA-256 hashes. Login is two-step when enabled (`/auth/totp/*`). Recovery codes are single-use.
- **Notification campaigns:** `notification_campaigns` + `NotificationCampaignService`; `POST /admin/notifications/campaign` validates the audience (cap 100k) and enqueues `process_notification_campaign` on ARQ (batched fan-out, never synchronous from the request).
- See `docs/admin-dashboard.md` for the full frontend architecture, routes, session handling (HttpOnly refresh cookie via Next.js BFF), and deployment.

---

## 16. Storage (photos)

- `StorageBackend` protocol (`put_object`, `delete_object`, `object_exists`, `presigned_upload_url`, `presigned_download_url`) with `LocalStorage` and `S3Storage` implementations (`app/services/storage.py`).
- Routers depend on the protocol via `get_storage()`; never reference boto3 in routers.
- Photo flow: `POST /profile/photos/upload-url` → client uploads to signed URL → `POST /profile/photos/confirm` records the object key as a `Photo` row. DB stores the object key, never image binary.
- `PhotoService.to_public_url()` converts stored keys to presigned/public URLs when serializing.

---

## 17. Workers (ARQ)

- Entrypoint `app/workers/arq_app.WorkerSettings` (a `Settings` dataclass instance). Run: `arq app.workers.arq_app.WorkerSettings`.
- Enqueue from app code with `app/workers/enqueue.py` helpers; they **fail-open** when the worker/Redis is down.
- Jobs: `send_email`, `send_sms`, `send_push_notification`, `process_photo_thumbnail`, `process_payment_webhook`, `expire_subscriptions`, `expire_profile_shares`, `expire_job_verifications`, `cleanup_deleted_accounts`, `process_notification_campaign`.
- Scheduling (e.g. daily expiry runs) is delegated to your orchestrator — tasks are functions to call, not cron.
- ARQ was chosen over Celery because the stack is fully async; jobs reuse the same async app code without serialization bridges.

---

## 18. Migrations workflow

1. Change the model.
2. `alembic revision --autogenerate -m "describe"` (needs a reachable DB; env.py reads `settings.DATABASE_URL`).
3. Review the generated file — it must be self-contained: use `sa.Uuid()`, `sa.DateTime(timezone=True)`, and `sa.JSON().with_variant(postgresql.JSONB(), 'postgresql')` for JSON columns (never `postgresql.JSONB()` bare, or SQLite rendering breaks).
4. `alembic upgrade head` then `alembic downgrade -1` on Postgres.
5. Note: `alembic check` reports spurious `CHAR(32) → GUID()` drift **on SQLite only** (dialect type rendering); it is a false positive — run `check` against Postgres.

---

## 19. Known pitfalls (checklist — do not reintroduce)

- `mapped_column(GUID, primary_key=True)` **without** `default=gen_uuid` → `NOT NULL constraint failed`.
- Attribute named `metadata` on any model → SQLAlchemy error; use `meta`.
- `self.refresh = RefreshTokenRepository(...)` inside `AuthService` shadows the `refresh()` method — the repo is named `self.refresh_repo`.
- Pydantic response schema with `id: str` + `from_attributes=True` → validation error; use `UUID`.
- Passing `str` where a `UUID` is expected into a GUID column → `'str' object has no attribute 'hex'`; let the `GUID` type coerce, or `UUID(...)` at the router.
- Naive vs aware datetime comparison on SQLite → normalize read-back datetimes with `tzinfo=timezone.utc`.
- Calling an async repo method without `await` (e.g. `MatchRepository.other_user_id` is intentionally **sync**).
- Forgetting `await session.commit()` in a router after a service mutation.
- Importing `get_session` from `app.db.session` instead of `app.api.deps` (breaks test overrides).
- Enum values passed as raw strings into `enum_column` columns — store/read `EnumClass` members; `.value` for serialization.
- Adding a scoring factor without a `WEIGHTS` key + `_REASON_MAP` entry → `KeyError`.
- Enqueueing jobs inside the request hot path is fine (they fail-open), but never `await` worker results — fire-and-forget only.
- `datetime.now(UTC)` vs SQLite naive values — normalize before comparing (see §6).
- Naming a repo method `list` shadows the builtin for class-body annotations (`list[Model]` → "not subscriptable" / "not valid as a type"). `AppConfigRepository` uses `list_configs`.
- Admin/verifier authorization must go through `require_role` (returns `403 FORBIDDEN`); don't hand-roll role checks or return 401.
- A service attribute `self.audit = AuditService(...)` shadows any `audit()` method on the same service (`'AuditService' object is not callable`) — name the method differently (e.g. `audit_trail`).
- Adding a second FK from a table to `users` makes `User.profile`/`Profile.user` ambiguous — declare `foreign_keys` on the relationship.
- `require_permission` depends on the session too — the endpoint must still declare `Depends(get_session)` (the session is shared/cached per request, not duplicated).
- Admin aggregates must use indexed/aggregate queries, never `SELECT *` + Python sums over the whole table (see `admin_analytics_service.py`).

---

## 20. Adding a new feature — checklist

1. **Model** in the right `app/db/models/*.py` module; export it in `app/db/models/__init__.py`; run the migration.
2. **Enum(s)** in `app/db/enums.py` if needed.
3. **Schema(s)** in `app/schemas/*.py` (request + response; `from_attributes=True` + `UUID` id fields).
4. **Repository** (only if non-trivial queries) extending `BaseRepository[T]`; export in `app/repositories/__init__.py`.
5. **Service** holding all business rules + authorization; take `AsyncSession`.
6. **Router** in `app/api/v1/`, using `Depends(get_current_user)`, `Depends(get_session)` (from `app.api.deps`), committing, returning `ApiResponse[...]`; register in `app/api/v1/__init__.py`.
7. **Admin endpoints** use `require_permission(...)`/`require_any_permission(...)` (never `require_role` for new dashboard routes) and record `ip_address`/`user_agent` via `get_request_context(request)` on mutations.
8. **Audit** sensitive actions via `AuditService.record`.
9. **Tests** in `tests/`, covering rules + authorization + edge cases.
10. Verify: `ruff check`, `ruff format`, `mypy app`, `pytest`, `alembic check` (Postgres).

---

## 21. Troubleshooting

| Symptom | Likely cause / fix |
| --- | --- |
| `NOT NULL constraint failed: users.id` | Missing `default=gen_uuid` on the PK column. |
| `Attribute name 'metadata' is reserved` | A model has a column attribute named `metadata`; rename to `meta`. |
| `'str' object has no attribute 'hex'` | `str` passed into a GUID column; coerce with `UUID(...)` or rely on the `GUID` type. |
| `ValidationError: Input should be a valid string` on `id` | Response schema used `id: str` with `from_attributes=True`; use `UUID`. |
| `TypeError: can't compare offset-naive and offset-aware` | Comparing a SQLite-read datetime to `datetime.now(UTC)`; normalize the naive value. |
| `<coroutine object ...> was never awaited` | An async repo/service method called without `await`. |
| 401 on everything in tests | `get_session` imported from `app.db.session` (breaks the test override). |
| `KeyError: '<factor>'` in scoring | A new scoring factor was added without a `WEIGHTS` key / `_REASON_MAP` entry. |
| `list` is not valid as a type in a repo | A repo method named `list` shadows the builtin; rename it (e.g. `list_configs`). |
| Admin endpoints return 401 for bad roles | Stale code path bypasses `require_role`; `require_role` must raise `ForbiddenError` → `403 FORBIDDEN`. |
| `alembic check` reports UUID drift | Only on SQLite (CHAR(32) vs GUID rendering); false positive — run against Postgres. |

---

## 22. Definition of done

- `pytest` → all green.
- `ruff check app migrations tests` → no findings.
- `mypy app` → no issues.
- Alembic migration committed for every schema change (`upgrade` + `downgrade` verified).
- Seed script updated if lookup data changed (keep it idempotent).
- No secrets committed; no business logic in routers; no raw ORM objects returned; sensitive fields gated.


---

## 23. AI Agent Operating Rules

This repository is an existing production-oriented codebase. Treat the current implementation and this `AGENTS.md` as the source of truth.

### Before making changes

1. Read `AGENTS.md` completely.
2. Read `docs/architecture.md`.
3. Inspect the existing implementation before creating new files.
4. Search for existing models, schemas, services, repositories, dependencies, enums, and tests before adding duplicates.
5. Understand existing patterns before modifying them.
6. Do not assume a feature is missing merely because it is not mentioned in the task — inspect the code first.

### Do not rewrite existing architecture unnecessarily

Do NOT:

* replace SQLAlchemy with another ORM
* replace PostgreSQL
* replace Pydantic
* replace FastAPI
* replace ARQ with Celery
* replace Redis
* introduce synchronous database access
* introduce a second architectural pattern
* reorganize the entire repository
* rename established modules without a compelling reason
* rewrite working code merely to make it stylistically different

Follow the existing architecture unless the task explicitly requests an architectural change.

---

### When implementing a feature

Work in small, verifiable increments.

Preferred order:

```text
Inspect existing code
        ↓
Determine affected domains
        ↓
Add/update enum
        ↓
Add/update model
        ↓
Create migration
        ↓
Add schema
        ↓
Add repository if needed
        ↓
Add service/business logic
        ↓
Add router
        ↓
Register router
        ↓
Add/update tests
        ↓
Run validation
```

Do not create unnecessary abstractions.

If an existing repository/service/helper already solves the problem, reuse it.

---

### Before editing a file

Inspect enough surrounding code to understand:

* imports
* naming conventions
* typing style
* existing dependencies
* transaction handling
* error handling
* authorization patterns
* test conventions

Do not make blind edits based only on filenames.

---

### Database changes

Any model/schema change that affects PostgreSQL must include an Alembic migration.

Never:

```python
Base.metadata.create_all(...)
```

as a replacement for migrations.

Before creating a migration:

1. Inspect existing migrations.
2. Follow the existing naming convention.
3. Generate or write the migration.
4. Review it manually.
5. Verify upgrade.
6. Verify downgrade.
7. Run the test suite.

Do not delete or rewrite historical migrations unless explicitly instructed.

---

### API changes

Before adding an endpoint:

1. Check whether an equivalent endpoint already exists.
2. Follow the existing URL naming conventions.
3. Use `ApiResponse[T]`.
4. Use Pydantic request/response schemas.
5. Use `get_current_user` for authenticated endpoints.
6. Use `get_session` from `app.api.deps`.
7. Put business logic in services.
8. Commit mutations in the router.
9. Add authorization tests.

Never return raw ORM objects.

---

### Authorization

For every endpoint involving a resource belonging to a user, explicitly determine:

```text
Who owns this resource?
Who is allowed to read it?
Who is allowed to modify it?
Can blocked users access it?
Can deleted/banned users access it?
Does profile privacy affect the response?
Does being matched change access?
Does admin/moderator role change access?
```

Do not assume authentication implies authorization.

A logged-in user is not automatically authorized to access another user's resource.

---

### Sensitive information

Before returning any user/profile data, verify the appropriate response schema.

Never accidentally expose:

```text
password_hash
refresh tokens
JWTs
phone_number
email
annual_income
exact coordinates
private family information
private horoscope information
internal verification information
payment information
admin information
audit information
```

unless the endpoint and authorization rules explicitly allow it.

When in doubt, return less information rather than more.

---

### Business rules

Business rules belong in services.

Do not add business logic such as:

```python
if user.is_premium:
    ...
```

directly to routers.

Instead:

```python
result = await SomeService(session).perform_action(...)
```

The service must determine:

* authorization
* subscription state
* verification state
* block state
* matching state
* privacy state
* business eligibility

The API layer should only translate HTTP requests into service calls.

---

### Transactions

Follow the existing transaction convention:

```text
Router
  ↓
Service
  ↓
Repository
  ↓
flush
  ↓
Router commit
```

Services may flush when IDs or database state are required.

Routers commit mutations.

Do not introduce arbitrary commits inside repositories.

Do not commit halfway through a business operation unless there is a clear transactional reason.

---

### Concurrency

When implementing operations that can race, think about concurrent requests.

This is particularly important for:

* creating matches
* processing payments
* refreshing tokens
* creating subscriptions
* job verification
* sending/swiping actions
* profile/photo updates

Database constraints and idempotency must be used where appropriate.

Do not rely solely on:

```python
if not exists:
    create()
```

because two concurrent requests can both observe `not exists`.

Use database uniqueness constraints, transactions, and/or appropriate locking where required.

---

### Payment code

Payment operations are security-sensitive.

Never trust:

```text
amount
currency
payment status
subscription status
verification status
provider transaction ID
```

from the mobile client.

Always resolve authoritative payment state server-side.

Webhook handlers must:

1. Verify the provider signature.
2. Parse the event.
3. Resolve the internal payment.
4. Be idempotent.
5. Update payment state.
6. Trigger downstream business transitions.
7. Avoid duplicate side effects.

Never activate premium access simply because the client says payment succeeded.

---

### File uploads

Never trust client-provided:

```text
filename
MIME type
extension
file size
image dimensions
```

Validate uploads server-side.

Do not store uploaded files directly inside the repository.

Use the configured `StorageBackend`.

Do not introduce direct `boto3` usage into routers or services when the existing storage abstraction can be used.

---

### Recommendation system

Do not bypass the existing recommendation pipeline.

Always preserve:

```text
Candidate Generation
        ↓
Hard Filters
        ↓
Scoring
        ↓
Ranking
        ↓
Feed
```

If adding a scoring factor:

1. Add the factor to `WEIGHTS`.
2. Add the corresponding `_REASON_MAP` entry.
3. Add tests.
4. Confirm the factor does not bypass hard preferences.
5. Consider performance impact.

Never silently add a scoring factor without updating the scoring configuration.

---

### Redis failures

Redis is not the primary database.

Where the existing architecture specifies fail-open behavior, preserve it.

A Redis outage should not unnecessarily make core functionality unavailable.

Examples:

```text
rate limiting
recommendation caching
OTP/reset temporary state
background job enqueueing
```

Do not turn a cache failure into a database failure unless the feature explicitly requires Redis as authoritative state.

---

### Background jobs

Do not perform expensive operations in the request path when an existing worker abstraction is appropriate.

Use the existing enqueue helpers.

Examples:

```text
email
SMS
push notifications
image processing
thumbnail generation
recommendation refresh
subscription expiry
verification expiry
cleanup
```

Workers must be idempotent where retries are possible.

Never assume a background job executes exactly once.

---

### Tests are part of the implementation

A feature is not complete when the code merely "looks correct."

Every new business rule must have tests.

At minimum test:

```text
happy path
invalid input
unauthorized access
ownership violation
blocked user
deleted/banned user
duplicate request
concurrent/idempotent behavior where relevant
privacy restrictions
```

Prefer testing through the service/API boundary rather than testing implementation details.

Do not weaken existing tests simply to make a new implementation pass.

---

### Existing tests are contracts

If an existing test fails after a change:

1. Determine whether the behavior should actually change.
2. If the behavior is intentionally changing, update the test and explain why.
3. If the behavior should not change, fix the implementation.

Never delete or weaken a test simply because it is inconvenient.

---

### Validation after changes

After implementation, run:

```bash
ruff format app migrations tests
ruff check app migrations tests
mypy app
pytest
```

If database-related changes were made and PostgreSQL is available:

```bash
alembic upgrade head
alembic check
alembic downgrade -1
alembic upgrade head
```

If a command cannot be run because an external dependency is unavailable, explicitly report that instead of pretending it passed.

Never claim a test or command passed unless it was actually executed.

---

### Keep changes focused

Do not modify unrelated files.

If a task asks for:

```text
"Add profile endpoint"
```

do not simultaneously:

* redesign authentication
* rewrite recommendations
* change database architecture
* rename models
* replace dependencies
* reformat the entire repository

unless the task requires it.

Prefer small, reviewable commits/changes.

---

### Error handling

Use existing `AppError` subclasses and error codes.

Do not return arbitrary error formats from individual endpoints.

Do not expose:

* SQL errors
* stack traces
* internal paths
* secrets
* provider credentials
* implementation details

to API clients.

---

### Documentation

When behavior changes materially:

* update `docs/architecture.md`
* update API documentation if necessary
* update `.env.example` for new configuration
* update seed data if lookup data changes
* update tests

Do not create documentation that contradicts the implementation.

---

### If requirements are ambiguous

Do not invent a large architecture.

First inspect:

```text
AGENTS.md
docs/architecture.md
existing models
existing services
existing schemas
existing tests
```

Then make the smallest change consistent with the existing system.

If an ambiguity materially affects data integrity, security, payments, privacy, or API compatibility, stop and ask for clarification rather than making a dangerous assumption.

For minor ambiguities, choose the most conservative behavior and document the assumption.

---

### Final response after completing a task

When reporting completed work, provide:

```text
## Implemented
- concise list of changes

## Files Changed
- relevant files only

## Database
- migration information, if applicable

## Tests
- commands actually run
- results

## Validation
- ruff result
- mypy result
- pytest result
- migration result if applicable

## Notes
- assumptions
- limitations
- follow-up work, if any
```

Do not claim success for commands that were not executed.

Do not include unnecessary implementation narration.

## The goal is to leave the repository in a **working, tested, migration-safe, secure, maintainable state** after every task.

## 24. Priority Order When Instructions Conflict

When deciding between competing instructions, use this priority:

```text
1. Security and data integrity
2. Explicit task requirements
3. This AGENTS.md
4. docs/architecture.md
5. Existing tests/contracts
6. Existing implementation conventions
7. Personal preference / stylistic improvements
```

Never sacrifice security, authorization, privacy, or data integrity merely to satisfy a stylistic preference.

If a task explicitly conflicts with an invariant in this document, call out the conflict before implementing the change.
