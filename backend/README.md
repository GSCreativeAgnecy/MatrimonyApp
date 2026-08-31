# Matchmaking API

Production-ready matrimony / matchmaking backend built with **FastAPI**, **SQLAlchemy 2.0 (async)**, **PostgreSQL**, **Redis**, **JWT**, **ARQ workers** and **Docker**.

Consumed primarily by a React Native mobile application. Designed to scale to hundreds of thousands to millions of users.

---

## Features

- **Modular architecture** ΓÇö clear separation of API / schemas / models / repositories / services.
- **Auth** ΓÇö Argon2id password hashing, JWT access + rotating refresh tokens, email/OTP verification, password reset, rate limiting via Redis, RBAC (`USER`, `MODERATOR`, `VERIFIER`, `ADMIN`, `SUPER_ADMIN`).
- **Profile & privacy** ΓÇö full profile domain, per-field privacy settings, distinct public / matched / own / admin response shapes (exact coordinates, income, contact details are never leaked).
- **Discovery** ΓÇö swipes (like / pass / super-like), automatic mutual-like match creation, deterministic recommendation engine (candidate generation ΓåÆ hard filters ΓåÆ scoring ΓåÆ ranking ΓåÆ feed) with a replaceable `ScoringEngine` and Redis caching.
- **Messaging** ΓÇö conversations + participants + messages with authorization; WebSocket-ready design.
- **Family, astrology, partner preferences, languages, interests** ΓÇö fully normalized, no comma-separated strings.
- **Monetization** ΓÇö subscription plans, subscriptions (premium derived from active subscription), payments via a pluggable provider (mock/stripe), provider webhooks as the only payment source of truth, paid job verification with database-driven pricing.
- **Trust & safety** ΓÇö blocks, reports, moderation, soft delete + anonymization job.
- **Admin APIs** ΓÇö users, bans, roles, reports, job verification review, subscriptions, payments, with role guards.
- **Audit logging** ΓÇö sensitive actions logged with actor, entity, IP and user-agent.
- **Workers (ARQ)** ΓÇö email/SMS/push, expiring subscriptions / shares / verifications, deleted-account cleanup, webhook processing.

## Tech Stack

| Concern | Choice |
| --- | --- |
| Language | Python 3.11+ (3.12 recommended) |
| API | FastAPI + Pydantic v2 |
| ORM | SQLAlchemy 2.0 (async) + asyncpg |
| DB | PostgreSQL (UUID PKs, `JSONB`, `timestamptz`) |
| Migrations | Alembic |
| Cache / rate-limit / denylist | Redis |
| Auth | PyJWT + Argon2id |
| Workers | ARQ (async-native, Redis broker) |
| Storage | S3-compatible or local filesystem (abstracted) |
| Tests | pytest + httpx + aiosqlite (no Postgres needed) |
| Lint / types | Ruff, mypy |

---

## Project Structure

```text
app/
Γö£ΓöÇΓöÇ main.py                 # FastAPI app, CORS, error handlers, static mount
Γö£ΓöÇΓöÇ config/                 # pydantic-settings + logging
Γö£ΓöÇΓöÇ db/
Γöé   Γö£ΓöÇΓöÇ base.py             # DeclarativeBase, GUID, JSONB, enum column helpers
Γöé   Γö£ΓöÇΓöÇ session.py          # async engine / session
Γöé   Γö£ΓöÇΓöÇ enums.py            # all domain enums
Γöé   ΓööΓöÇΓöÇ models/             # one module per domain
Γö£ΓöÇΓöÇ api/
Γöé   Γö£ΓöÇΓöÇ deps.py             # get_session, get_current_user, require_role, rate_limit
Γöé   Γö£ΓöÇΓöÇ errors.py           # consistent error envelope + handlers
Γöé   ΓööΓöÇΓöÇ v1/                 # routers (auth, profiles, swipes, matches, ...)
Γö£ΓöÇΓöÇ schemas/                # Pydantic request/response models
Γö£ΓöÇΓöÇ repositories/           # data-access layer
Γö£ΓöÇΓöÇ services/               # business logic (auth, swipe, recommendation, payment, ...)
Γö£ΓöÇΓöÇ workers/                # ARQ settings + tasks + enqueue helpers
Γö£ΓöÇΓöÇ security/               # jwt, password, redis, rate limiting
ΓööΓöÇΓöÇ seed.py                 # idempotent seed script

migrations/                 # Alembic (async env.py + initial migration)
tests/                      # pytest suite (SQLite)
```

## Quick Start (Docker)

```bash
docker compose up --build
```

This starts `api`, `worker`, `postgres`, `redis`, and a one-shot `migrate` service (runs `alembic upgrade head` + seed).

- API: http://localhost:8000
- Docs (dev): http://localhost:8000/docs

## Manual Setup

### 1. Create a virtual environment and install

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```ini
DATABASE_URL=postgresql+asyncpg://matchmake:matchmake@localhost:5432/matchmaking
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=<long-random-string>
```

Never commit `.env`.

### 3. Start PostgreSQL

```bash
docker compose up -d postgres
```

or use any local Postgres instance.

### 4. Start Redis

```bash
docker compose up -d redis
```

or `redis-server`.

### 5. Run migrations

```bash
alembic upgrade head
```

Check for schema drift (Postgres):

```bash
alembic check
```

### 6. Seed data (idempotent)

```bash
python -m app.seed
```

Seeds languages, religions, castes, countries, states, education levels, occupations, interests, subscription plans and verification pricing.

### 7. Start the API

```bash
uvicorn app.main:app --reload
```

### 8. Run the worker

```bash
arq app.workers.arq_app.WorkerSettings
```

### 9. Run tests

```bash
pytest
```

Tests use an in-memory SQLite database ΓÇö no Postgres or Redis required.

### 10. Lint / format / type-check

```bash
ruff check app migrations tests
ruff format app migrations tests
mypy app
```

## Environment Variables

See `.env.example` for the full list. Highlights:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Async SQLAlchemy Postgres URL |
| `REDIS_URL` | Redis for rate limiting, OTP/reset state, denylist, caches |
| `JWT_SECRET_KEY` / `JWT_ALGORITHM` | JWT signing (HS256). Rotate in production. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` | Token lifetimes |
| `STORAGE_BACKEND` | `local` (dev) or `s3` |
| `S3_*` | S3-compatible storage settings |
| `PAYMENT_PROVIDER` | `mock` (dev) or `stripe` |
| `PAYMENT_WEBHOOK_SECRET` | Webhook signature verification |
| `SMTP_*`, `SMS_*` | Email / SMS delivery |
| `LOGIN_RATE_LIMIT`, `OTP_RATE_LIMIT` | Redis-backed rate limits |

## API Overview

All endpoints live under `/api/v1` and return a consistent envelope:

```json
{
  "data": {},
  "meta": {}
}
```

Errors:

```json
{
  "error": { "code": "PROFILE_NOT_FOUND", "message": "Profile not found" }
}
```

### Auth
```
POST /api/v1/auth/register          POST /api/v1/auth/login
POST /api/v1/auth/refresh           POST /api/v1/auth/logout
POST /api/v1/auth/forgot-password   POST /api/v1/auth/reset-password
POST /api/v1/auth/verify-email      POST /api/v1/auth/send-otp
POST /api/v1/auth/verify-otp        GET  /api/v1/auth/me
POST /api/v1/auth/change-password
```

### Profile & photos
```
GET    /api/v1/profile/me           POST   /api/v1/profile
PATCH  /api/v1/profile              DELETE /api/v1/profile
GET    /api/v1/profile/privacy      PATCH  /api/v1/profile/privacy
GET    /api/v1/profile/photos       POST   /api/v1/profile/photos/upload-url
POST   /api/v1/profile/photos/confirm
PATCH  /api/v1/profile/photos/{id}  DELETE /api/v1/profile/photos/{id}
GET    /api/v1/profiles/{user_id}   GET    /api/v1/profiles/{user_id}/contact
```

### Discovery
```
GET  /api/v1/recommendations        POST /api/v1/swipes
GET  /api/v1/matches                DELETE /api/v1/matches/{id}
```

### Messaging
```
GET  /api/v1/conversations          POST /api/v1/conversations
GET  /api/v1/conversations/{id}/messages
POST /api/v1/conversations/{id}/messages
POST /api/v1/conversations/{id}/read
```

### Family / astrology / preferences
```
GET/PUT /api/v1/family                     GET/PUT /api/v1/astrology
POST /api/v1/astrology/calculate
GET/PUT /api/v1/preferences
```

### Trust & safety
```
GET/POST/DELETE /api/v1/blocks[...]        POST /api/v1/reports
GET /api/v1/notifications                  POST /api/v1/notifications/{id}/read
POST /api/v1/notifications/read-all        GET /api/v1/notifications/unread-count
```

### Monetization & verification
```
GET /api/v1/subscription/plans             GET /api/v1/subscription
POST /api/v1/subscription/checkout
POST /api/v1/payments/webhook/{provider}
POST /api/v1/verifications/job             GET /api/v1/verifications
POST /api/v1/profile-shares                GET/DELETE /api/v1/profile-shares[...]
```

### Admin (`ADMIN`/`MODERATOR`/`VERIFIER`)
```
GET  /api/v1/admin/users                   POST /api/v1/admin/users/{id}/ban
POST /api/v1/admin/users/{id}/unban        POST /api/v1/admin/users/{id}/role
GET  /api/v1/admin/reports                 POST /api/v1/admin/reports/{id}/review
GET  /api/v1/admin/verifications/job       POST /api/v1/admin/verifications/job/{id}/review
GET  /api/v1/admin/subscriptions           GET /api/v1/admin/payments
```

Interactive docs are available at `/docs` (development) and `/openapi.json`.

## Authentication Design

- **Access token** (short-lived JWT, ~15 min) is sent as `Authorization: Bearer <token>`.
- **Refresh token** (long-lived JWT) is rotated on every `/auth/refresh` ΓÇö the old token's server record is revoked (rotation + reuse detection via `refresh_tokens` table).
- Password hashes use **Argon2id**.
- Email verification and password-reset tokens are stored in Redis with TTLs; OTP flows are rate-limited.
- `get_current_user` resolves the token to a live, non-banned, non-deleted user. Roles gate admin/verifier endpoints.
- Client-supplied `user_id`, premium / payment / verification state is **never trusted** ΓÇö always derived server-side.

## Recommendation Architecture

```
Candidate Generation -> Hard Filters -> Compatibility Scoring -> Ranking -> Feed
```

- Hard filters: self/blocked/banned/deleted/already-swiped/already-matched excluded, plus REQUIRED preferences (religion, caste, country) and age range.
- Scoring: deterministic weighted factors (age, height, location, religion, caste, language, education, occupation, diet, smoking, drinking, family values, interests, marital status, intent).
- Response: `{candidate_user_id, score, reason_codes}`.
- `ScoringEngine` is a `Protocol` ΓÇö swap in an ML model later without touching the pipeline.
- The per-user feed is cached in Redis (TTL 15 min).

## Payments & Verification Architecture

- `PaymentProvider` protocol (`mock`, `stripe`) ΓÇö webhooks are the only source of truth; status is verified and applied idempotently by `provider_payment_id`.
- Successful subscription payment ΓåÆ subscription created/extended (`is_premium` is derived, never stored as a source of truth).
- Job verification is paid: pricing is read from the `app_config` table (`LOCAL_JOB_VERIFICATION_PRICE`, `NRI_JOB_VERIFICATION_PRICE`).
- Verification status changes only via `VERIFIER`/`ADMIN` review or trusted webhook transitions.

## Workers (ARQ)

ARQ was chosen over Celery because the stack is fully async ΓÇö ARQ is async-native and Redis-based, so background jobs reuse the exact same async app code without serialization bridges.

Jobs: `send_email`, `send_sms`, `send_push_notification`, `process_photo_thumbnail`, `process_payment_webhook`, `expire_subscriptions`, `expire_profile_shares`, `expire_job_verifications`, `cleanup_deleted_accounts`.

Cron/scheduling is left to your orchestrator (e.g. run `expire_*` jobs on a schedule).

## Security & Privacy Notes

- No plaintext secrets; `.env` is git-ignored.
- Sensitive fields (phone, email, income, exact location, DOB, family, horoscope, photos, employment) are gated behind explicit authorization and privacy settings.
- Ownership checks on every resource (photos, preferences, family, matches, conversations).
- Object-level authorization enforced in services; routers never trust client IDs for authorization.
- Rate limiting on auth/OTP; fail-open so a Redis outage never bricks login.
- Global exception handler never leaks stack traces.

## Scaling Considerations

- UUID PKs, functional indexes on hot paths (see `docs/architecture.md`).
- Discovery queries use index-backed filters; the feed is cached.
- Messaging/WebSockets can be layered onto the existing conversation model.
- The recommendation engine is designed to be replaced by an ML model.
- Payments/subscriptions use idempotent, webhook-driven state transitions.
