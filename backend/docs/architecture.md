# Architecture Design

## 1. Overall Architecture

Modular layered application:

```
API layer (FastAPI routers) -> Schemas (Pydantic) -> Services (business logic)
        -> Repositories (data access) -> SQLAlchemy ORM -> PostgreSQL
                           |-> Redis (rate limiting, cache, presence, denylist)
                           |-> Object storage (S3-compatible) for photos
                           |-> ARQ worker (background jobs)
```

- Routers contain **no business logic**; they parse/validate requests and return schema responses.
- Services contain business rules and orchestration.
- Repositories encapsulate query construction for reuse.
- Pydantic schemas are the only payloads crossing the API boundary (never raw ORM objects).

## 2. Table List

| Domain | Tables |
| --- | --- |
| Auth / Account | `users` |
| Profile | `profiles`, `user_privacy_settings` |
| Photos | `photos` |
| Languages | `languages`, `user_languages` |
| Interests | `interests`, `user_interests` |
| Family | `families`, `family_members` |
| Astrology | `astrology_profiles` |
| Preferences | `partner_preferences`, `preferred_religions`, `preferred_castes`, `preferred_languages`, `preferred_countries`, `preferred_states`, `preferred_diets` |
| Discovery | `swipes`, `matches` |
| Messaging | `conversations`, `conversation_participants`, `messages` |
| Blocks / Reports | `blocks`, `reports` |
| Notifications | `notifications` |
| Monetization | `subscription_plans`, `subscriptions`, `payments`, `job_verifications` |
| Sharing | `profile_shares` |
| Governance | `audit_logs` |
| Lookups (seeded) | `religions`, `castes`, `languages`, `countries`, `states`, `education_levels`, `occupations`, `interests`, `app_config` |

## 3. Enums

- `AccountStatus`: PENDING, ACTIVE, SUSPENDED, BANNED, DELETED
- `UserRole`: USER, MODERATOR, VERIFIER, ADMIN, SUPER_ADMIN
- `Gender`: MALE, FEMALE, OTHER
- `MaritalStatus`: NEVER_MARRIED, DIVORCED, WIDOWED, AWAITING_DIVORCE
- `Diet`: VEGETARIAN, NON_VEGETARIAN, EGGITARIAN, JAIN, VEGAN
- `Drinking`, `Smoking`: NEVER, OCCASIONALLY, REGULARLY, PREFER_NOT_TO_SAY
- `PhysicalStatus`: NORMAL, PHYSICALLY_CHALLENGED
- `EmploymentStatus`: EMPLOYED, SELF_EMPLOYED, BUSINESS_OWNER, STUDENT, NOT_WORKING, RETIRED, HOMEMAKER
- `Intent`: MARRIAGE, FRIENDSHIP, DATE, NOT_SURE
- `ProfileCreatedBy`: SELF, PARENT, GUARDIAN, RELATIVE, FRIEND, PROFILE_SERVICE
- `BodyType`: SLIM, AVERAGE, ATHLETIC, HEAVY
- `Complexion`: FAIR, WHEATISH, DARK, VERY_FAIR, MIDDLE_BROWN
- `PhotoVerificationStatus`: UNVERIFIED, PENDING, VERIFIED, REJECTED
- `PhotoVisibility`: PUBLIC, PRIVATE
- `PreferenceLevel`: REQUIRED, PREFERRED, NO_PREFERENCE
- `SwipeAction`: LIKE, PASS, SUPER_LIKE
- `MatchStatus`: ACTIVE, UNMATCHED, BLOCKED, EXPIRED
- `MessageType`: TEXT, IMAGE, SYSTEM
- `ReportStatus`: PENDING, UNDER_REVIEW, RESOLVED, DISMISSED
- `ReportReason`: FAKE_PROFILE, SCAM, HARASSMENT, INAPPROPRIATE_CONTENT, SPAM, UNDERAGE, IMPERSONATION, OTHER
- `NotificationType`: NEW_MATCH, NEW_MESSAGE, NEW_LIKE, PROFILE_VIEW, VERIFICATION_COMPLETE, SUBSCRIPTION_EXPIRING, SYSTEM
- `SubscriptionStatus`: TRIAL, ACTIVE, PAST_DUE, CANCELED, EXPIRED
- `PaymentStatus`: PENDING, SUCCESS, FAILED, REFUNDED, CANCELLED
- `PaymentType`: SUBSCRIPTION, JOB_VERIFICATION, OTHER
- `JobVerificationStatus`: PENDING_PAYMENT, UNDER_REVIEW, VERIFIED, REJECTED, EXPIRED
- `EmploymentType`: LOCAL, NRI
- `SharePermission`: VIEW, CONTACT, MANAGE
- `FamilyType`: JOINT, NUCLEAR, EXTENDED
- `AstrologyDosham`: NONE, MANGAL, PARTHIV, OTHER

## 4. Foreign Keys (main)

- `profiles.user_id` -> `users.id` (unique, cascade delete)
- `user_privacy_settings.user_id` -> `users.id` (unique)
- `photos.user_id` -> `users.id`
- `user_languages.user_id`/`language_id` (unique pair)
- `user_interests.user_id`/`interest_id` (unique pair)
- `families.user_id` -> `users.id` (unique)
- `family_members.user_id` -> `users.id`
- `astrology_profiles.user_id` -> `users.id` (unique)
- `partner_preferences.user_id` -> `users.id` (unique)
- preferred_* tables -> `partner_preferences.id`
- `swipes.from_user_id`/`to_user_id` -> `users.id` (unique `(from, to, action)` only for non-pass; pass rows may repeat)
- `matches.user1_id`/`user2_id` -> `users.id` (unique pair, normalized order `user1_id < user2_id`)
- `conversation_participants.conversation_id`/`user_id` (unique pair)
- `messages.conversation_id`, `messages.sender_id`
- `blocks.blocker_id`/`blocked_id` (unique pair)
- `reports.reporter_id`/`reported_user_id`
- `notifications.user_id`
- `subscriptions.user_id`/`plan_id`
- `payments.user_id`
- `job_verifications.user_id`, `payment_id`
- `profile_shares.owner_user_id`/`shared_with_user_id`
- `audit_logs.actor_user_id` (nullable for system actions)

## 5. Index Strategy

Functional indexes on hot query paths (see migration):
- `users`: email, phone_number, account_status, last_active_at, deleted_at
- `profiles`: user_id (unique), gender, date_of_birth, city, country, religion, caste, (gender, is_active, deleted_at)
- `swipes`: (from_user_id, to_user_id), to_user_id, (from_user_id, created_at) for feed ordering
- `matches`: user1_id, user2_id, (status)
- `messages`: (conversation_id, created_at), conversation_id + deleted_at
- `notifications`: (user_id, is_read), (user_id, created_at)
- `subscriptions`: (user_id, status), (plan_id, status)
- `payments`: provider_payment_id (unique), user_id, status
- `reports`: reported_user_id, status
- `job_verifications`: user_id, status
- `blocks`: (blocker_id, blocked_id) unique

## 6. Auth / Authorization Design

- Argon2id password hashing (argon2-cffi).
- JWT (HS256) access tokens (~15 min) + refresh tokens (~30 days) with rotation.
- Refresh token `jti` denylist in Redis; rotation revokes previous token.
- OTP verification for email/phone uses Redis-backed codes with expiry and rate limiting.
- RBAC roles on `users.role`: USER, MODERATOR, VERIFIER, ADMIN, SUPER_ADMIN.
- `current_user` dependency resolves token -> user; ownership checks in services.
- Client-supplied `user_id`, premium/payment/verification state is NEVER trusted; always derived server-side.

## 7. Recommendation Architecture

```
Candidate Generation (active, verified, eligible gender, not self)
        -> Hard Filters (religion REQUIRED, caste REQUIRED, age range, marital status,
                         location radius, exclude swiped/matched/blocked)
        -> Compatibility Scoring (weighted deterministic: age, height, location, religion,
                                  caste, mother tongue, education, occupation, diet,
                                  smoking, drinking, family values, interests, intent)
        -> Ranking (score desc)
        -> Feed (Redis-cached per user, TTL)
```
Returns `{candidate_user_id, score, reason_codes}`. The `ScoringEngine` is a replaceable protocol so an ML model can be swapped in later.

## 8. Payment / Verification Architecture

- `PaymentProvider` protocol (Stripe/Razorpay pluggable); webhooks are the only source of truth.
- Webhook signature verified; idempotent by `provider_payment_id`; `payments` + `subscriptions`/`job_verifications` transition atomically.
- Pricing from `app_config` table (keys `pricing.local_job_verification=119`, `pricing.nri_job_verification=199`, with legacy-key and settings fallbacks) — never hardcoded.
- `job_verifications` status machine: `PENDING_PAYMENT -> UNDER_REVIEW -> VERIFIED | REJECTED`. Only VERIFIER/ADMIN roles transition verification status.

## 9. Worker Architecture (ARQ)

Chosen **ARQ** over Celery because the codebase is fully async (`asyncpg`, `async` SQLAlchemy) and ARQ is Redis-native, async-first, and lightweight. Celery has poor asyncio support and adds heavyweight broker infra. Jobs run in a separate container via `arq worker.WorkerSettings`.

Jobs: send_email, send_sms, send_push_notification, expire_subscriptions, expire_profile_shares, expire_job_verifications, cleanup_deleted_accounts, process_photo (thumbnails), process_payment_webhook.

## 10. Database Notes

- UUID PKs (Postgres `gen_random_uuid()`).
- `timestamptz` everywhere; `JSONB` for structured payloads (via `JSON().with_variant(JSONB, "postgresql")` for portability to SQLite in tests).
- Soft delete on `users` (`deleted_at`, `account_status=DELETED`) with a background anonymization job.
- Check constraints for range validity (e.g. `age_min < age_max`).

## 11. Remote App Configuration

The `app_config` table is the backend-managed configuration source for the React
Native app (branding, feature flags, public limits/pricing, app versions,
maintenance state, legal/support links).

```
React Native App
       │
       │ GET /api/v1/app/config   (public, no auth)
       ▼
FastAPI -> AppConfigService
              ├── Redis cache  (key: app_config:public, TTL: settings.APP_CONFIG_CACHE_TTL)
              └── PostgreSQL app_config
```

### Model

`app_config` columns: `id`, `key` (unique, indexed), `value` (JSONB — strings,
numbers, booleans or structured JSON), `value_type` (`ConfigValueType`:
STRING/INTEGER/FLOAT/BOOLEAN/JSON), `category` (`ConfigCategory`:
BRANDING/APP/FEATURES/LIMITS/PRICING/VERSIONS/LEGAL/SUPPORT), `is_public`,
`is_active`, `description`, `updated_by` (FK users), `created_at`, `updated_at`.

Known keys are centralized in `app/services/app_config_keys.py`
(`CONFIG_KEY_SPECS`) and are the single source for seeds and validation.

### Public endpoint

`GET /api/v1/app/config` — **no authentication**. Returns only entries with
`is_public=true` and `is_active=true`, grouped by category:

```json
{
  "data": {
    "branding": { "app_name": "MyMatrimony", "primary_color": "#7C3AED", ... },
    "app": { "maintenance_mode": false, "maintenance_message": null },
    "features": { "registration": true, "video_calls": false, ... },
    "limits": { "max_photos": 6, "max_daily_swipes": 50 },
    "pricing": { "local_job_verification": 119, "nri_job_verification": 199 },
    "versions": { "minimum_ios_version": "1.0.0", "force_update_ios": false, ... },
    "legal": { "privacy_url": null, ... },
    "support": { "email": null, "phone": null }
  },
  "meta": { "version": "<sha256[:16] of public payload>" }
}
```

- `meta.version` is a deterministic content hash — it changes whenever public
  configuration changes. The mobile app uses it to detect stale local caches.
- Response schemas (`app/schemas/app_config.py`) use `extra="allow"` and stable
  field names, so new keys can be added without breaking older clients.
- DB `features.enable_*` keys map to friendly public names (`features.registration`).

### Admin endpoints

`/api/v1/admin/app-config` — only `ADMIN` / `SUPER_ADMIN` (via `require_role`).

- `GET /` list with filters `category`, `is_public`, `is_active` + `limit`/`offset`.
- `GET /{key}`, `POST /`, `PATCH /{key}`, `DELETE /{key}`.
- `key` and `value_type` are immutable after creation. `DELETE` performs a soft
  deactivation (`is_active=false`).
- Validation: key format `category.name`, value matches `value_type`, category is
  a known member, hex colors for `*_color` keys, duplicate key → `409`.

### Caching & versioning

- Public config is cached in Redis under `app_config:public` (TTL 900s).
- Every admin mutation: update PostgreSQL → commit → invalidate the Redis cache →
  record an audit event (`app_config.created/updated/deactivated`).
- All Redis interactions **fail open**: if Redis is unavailable the public
  endpoint reads PostgreSQL directly and never fails.

### Security boundaries

- Only `is_public=true` entries ever leave via the public endpoint. Private
  entries (and the `id`, `updated_by`, audit fields) are admin-only.
- `app_config` is **not** a secret store — secrets live in environment variables.
- Feature flags drive UI/UX only; they are **not** authorization. Server-side
  services independently enforce subscription, verification and payment rules.
- Public pricing is display-only. Payment endpoints always read the authoritative
  server-side price and never accept an amount from the client.

### React Native caching contract

```
App startup
  → load locally cached config
  → render app immediately
  → GET /api/v1/app/config
      on success: store new config + version, update UI
      on failure: continue using cached config
```

The backend does not implement client-side storage; it only guarantees a stable,
versioned, predictable payload.

## 12. Admin Dashboard

The **admin web dashboard** is a separate Next.js application under `admin/`. It is a
pure client of the FastAPI API — it never connects to PostgreSQL, never holds
database credentials, and never enforces authorization itself.

```
React Native Mobile App          Admin Web Dashboard (Next.js, admin/)
        │                                │
        │                                │ HTTPS (BFF auth routes + API calls)
        ▼                                ▼
   FastAPI API (single backend, authoritative)
        │
        ├── PostgreSQL
        ├── Redis
        └── ARQ Workers
```

### Authorization model: Role → Permissions

The backend extended `UserRole` with `SUPPORT`, `FINANCE` and `ANALYST` and added a
permission model:

- `app/security/permissions.py` — the permission registry: `ALL_PERMISSIONS`
  (e.g. `users.read`, `users.suspend`, `payments.refund`, `messages.read_private`,
  `app_config.update`, `admin_users.manage`) and the default `ROLE_PERMISSIONS` map.
- `role_permissions` table (`app/db/models/admin.py`) — runtime-overridable
  Role → Permission rows seeded from the registry.
- `require_permission(...)` / `require_any_permission(...)` dependencies in
  `app/api/deps.py` — the backend checks `PermissionService.permissions_for_role`
  (DB rows, falling back to the static registry) on every admin route.
- The dashboard **only hides UI** (`PermissionGate`); the API enforces.

Admin roles and their default permissions:

| Role | Typical access |
| --- | --- |
| SUPER_ADMIN | all permissions (non-strippable) |
| ADMIN | all permissions |
| MODERATOR | users.*, profiles.*, photos.moderate, reports.*, messages.read_private |
| VERIFIER | verification.*, job_verification.*, photos.moderate, profiles.read |
| SUPPORT | users.read/update, reports.*, messages.read_private, notifications.send |
| FINANCE | payments.read/refund, subscriptions.*, analytics.read |
| ANALYST | analytics.read, audit_logs.read, users.read, payments.read, subscriptions.read |

### Admin API surface

All admin routes live under `/api/v1/admin/*` and return the `ApiResponse` envelope:

| Router | Endpoints |
| --- | --- |
| `admin_dashboard.py` | `/admin/dashboard/{summary,action-center,recent-activity,user-growth,engagement,revenue,moderation}` |
| `admin_users.py` | `/admin/users` list+filters, `/admin/users/{id}` detail, sub-resources (`profile`, `photos`, `verifications`, `matches`, `conversations`, `payments`, `reports`, `audit`), actions (`suspend`, `ban`, `unban`, `delete`, `restore`, `verify`, `role`) |
| `admin_moderation.py` | `/admin/profiles`, `/admin/photos`, `/admin/reports`, `/admin/profile-shares` |
| `admin_matches.py` | `/admin/matches` |
| `admin_messages.py` | `/admin/messages/conversations` — private message access requires `messages.read_private` and writes an `admin.message_view` audit event |
| `admin_payments.py` | `/admin/payments`, `/admin/payments/{id}`, `/admin/payments/{id}/refund` |
| `admin_subscriptions.py` | `/admin/subscriptions`, `/admin/subscription-plans` CRUD |
| `admin_verification.py` | `/admin/verifications/job` list/detail/review/request-info |
| `admin_notifications.py` | `/admin/notifications/campaign` + `/campaigns` |
| `admin_analytics.py` | `/admin/analytics/{users,engagement,matching,revenue,moderation}` |
| `admin_audit.py` | `/admin/audit-logs` (read-only) |
| `admin_admin_users.py` | `/admin/admin-users`, `/admin/roles` (+ role permission management) |
| `admin_app_config.py` | `/admin/app-config` (pre-existing) |

### 2FA

- Opt-in TOTP (RFC 6238) via `app/services/totp_service.py` (pyotp).
- `user_totp_secrets` + `totp_recovery_codes` tables; recovery codes stored as
  SHA-256 hashes only.
- Login is two-step: `POST /auth/login` returns `{requires_2fa, mfa_token}` when
  enabled; `POST /auth/totp/verify` validates a TOTP/recovery code and issues tokens.
- Endpoints: `/auth/totp/{setup,status,enable,disable}`, `/auth/totp/verify`.

### Sessions (frontend)

- Access tokens live in browser memory only (never localStorage).
- The refresh token is stored in an HttpOnly, SameSite=Strict cookie set by Next.js
  BFF route handlers under `admin/app/api/auth/*` (`login`, `totp`, `refresh`,
  `logout`). The client auto-refreshes on 401 via `/api/auth/refresh`.

### Notification campaigns

- `notification_campaigns` table + `NotificationCampaignService`.
- `POST /admin/notifications/campaign` validates the audience (max 100k users),
  records the campaign, and enqueues `process_notification_campaign` on ARQ.
- The worker resolves the audience and creates notifications in batches of 1000;
  nothing is sent synchronously from the HTTP request.

### Security invariants

- The dashboard never holds secrets: no `DATABASE_URL`, `JWT_SECRET_KEY`,
  `PAYMENT_API_KEY`, webhook secrets, S3/SMTP credentials reach the browser.
- Payments/subscription/verification/premium state is always resolved server-side;
  the client can never assert its own status.
- Every sensitive action (suspend, ban, delete, refund, moderation, private message
  access, role changes, config edits) writes an audit log with actor + IP/UA.
- Profile `review_status` and job-verification `reviewer_notes` are moderation
  ledgers; discovery enforcement for review status is a documented follow-up.
