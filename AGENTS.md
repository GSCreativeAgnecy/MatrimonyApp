# AGENTS.md — Ardhang Matrimony (monorepo)

Guidance for AI agents and developers working anywhere in this repository. **Read this file first, then the sub-app guide that owns the area you are touching.**

| App | Directory | Sub-guide | Authoritative for |
| --- | --- | --- | --- |
| Backend API | `backend/` | `backend/AGENTS.md` | all API contracts, data model, auth, payments, privacy |
| Admin dashboard | `admin/` | this file | admin UI only (pure API client) |
| End-user web | `web/` | this file | web UI only (pure API client) |
| Mobile app | `mobile/` | `mobile/AGENTS.md` | mobile UI only (pure API client) |

`backend/AGENTS.md` is the deepest and most binding document — API shape, authorization, business rules, pricing, and privacy are defined there. When this file and `backend/AGENTS.md` disagree about backend behavior, `backend/AGENTS.md` wins.

---

## 1. What this project is

A production matrimony/matchmaking platform:

- **`backend/`** — FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + Redis + Alembic + ARQ workers. Serves `/api/v1/*`, `/static/*` (local storage photos) and `/health`. The only component that talks to the database.
- **`admin/`** — Next.js 14 dashboard for staff (users, moderation, payments, verifications, analytics, app config). Pure API client; auth via a same-origin Node BFF with an HttpOnly refresh cookie.
- **`web/`** — Next.js 14 end-user client (discover, matches, chat, profile). Pure API client; same BFF auth pattern as admin.
- **`mobile/`** — Expo SDK 57 / React Native app. Tokens in `expo-secure-store`.

**Golden rule:** the backend is authoritative. Clients never re-implement business rules and never trust client-supplied premium/verification/payment/role state. UI gating is convenience only.

---

## 2. Non-negotiable rules

1. **Never trust the client** for `user_id`, roles, premium/subscription state, payment status, verification status, or uploaded file type/size/filename.
2. **Never commit secrets.** `.env` files are git-ignored; extend `.env.example` when adding config.
3. **API envelopes are fixed:** success `{"data": ..., "meta": ...}`, errors `{"error": {"code", "message", "details?"}}`. Never invent other shapes.
4. **Payments come only from verified provider webhooks.** Signature verification uses the raw request body. Production refuses to boot with the mock provider (see `backend/AGENTS.md` §15).
5. **Privacy shapes are a contract:** own / public / matched / admin profile responses never blur (see `backend/AGENTS.md` §11).
6. **Photos** are validated server-side (magic bytes, size limit, `photos/{user_id}/` key ownership, object existence) and stored via the `StorageBackend` abstraction — never binaries in the DB, never client keys without validation.
7. **Redis is fail-open** for rate limiting, caches, OTP state, and job enqueueing. A Redis outage must not break login or core flows.
8. **Migrations, not `create_all`.** Every schema change ships an Alembic migration verified `upgrade` + `downgrade` (see `backend/AGENTS.md` §18).
9. **Keep changes focused.** Small, reviewable increments; run the validation commands for the app you touched before reporting done.
10. **Never claim validation passed unless you actually ran it.**

---

## 3. Repo layout

```text
.
├── backend/            # FastAPI API, workers, migrations, tests, docker-compose.yml, nginx
│   ├── app/            # api/ schemas/ models/ repositories/ services/ workers/ security/
│   ├── migrations/     # Alembic
│   ├── tests/          # pytest (SQLite in-memory; no Postgres/Redis needed)
│   ├── docs/           # architecture.md, admin-dashboard.md
│   ├── docker/         # nginx.conf + Dockerfile for the public proxy
│   └── docker-compose.yml  # THE deployment stack (api, worker, admin, web, postgres, redis, proxy)
├── admin/              # Next.js admin dashboard + BFF routes (app/api/auth/*)
├── web/                # Next.js end-user web client + BFF routes (app/api/auth/*)
└── mobile/             # Expo React Native app
```

Deployment topology (docker-compose, deployed via Coolify):

- `proxy` (nginx) is the single public origin. It routes `/api/*` and `/static/*` → `api:8000`, `/api/auth/*` and everything else → `admin:3001`.
- `web` is intentionally **not** routed by the admin proxy — it is served on its own public domain (build arg `PUBLIC_API_BASE_URL`).
- Admin BFF calls the API server-side via `ADMIN_API_URL=http://api:8000`; web BFF via `WEB_API_URL=http://api:8000`.
- Required production env: `POSTGRES_PASSWORD`, `JWT_SECRET_KEY` (≥32 random chars), `PAYMENT_PROVIDER` + `PAYMENT_API_KEY` + `PAYMENT_WEBHOOK_SECRET` (Stripe), optionally `ALLOW_MOCK_PAYMENTS=true` for demos only, `TRUSTED_PROXY_COUNT=2` behind the double proxy.

---

## 4. Commands per app

### All apps, one shot (Windows local testing)

```bat
run.cmd                # API (:8000, SQLite) + admin (:3001) + web (:3000) + mobile (Expo)
run.cmd --no-mobile    # skip the Expo dev server
run.cmd api|admin|web|mobile   # start a single app
```

`run.cmd` opens one window per app. The API runs on SQLite (`backend/dev.db`) with the mock payment provider and `ENQUEUE_JOBS=false`, so no Docker/Postgres/Redis is required; Redis-backed features fail open. First run creates `backend/.venv` and installs npm dependencies. It also seeds a local-only admin: `admin@example.com` / `ChangeMe123!` (SUPER_ADMIN).

### Backend (`backend/`)

```bash
.venv\Scripts\activate            # Windows
pip install --group dev -e .      # package + dev tools (PEP 735; pip >= 25.1)

pytest                            # full suite (SQLite, no Postgres/Redis)
ruff check app migrations tests
ruff format app migrations tests
mypy app
python -m app.seed                # idempotent seed
uvicorn app.main:app --reload     # run API
arq app.workers.arq_app.WorkerSettings   # run worker
docker compose up --build         # full stack
```

### Admin (`admin/`) and Web (`web/`)

```bash
npm ci
npm run typecheck                 # tsc --noEmit (admin + mobile have this script)
node node_modules/next/dist/bin/next build   # validate production build (web/admin)
```

### Mobile (`mobile/`)

```bash
npm ci
npm run typecheck
npx expo-doctor
npx expo export --platform android
```

**CI definition of done:** `pytest` green + `ruff check` clean + `mypy app` clean (backend); `tsc --noEmit` clean for admin/web/mobile. The workflow lives in `.github/workflows/ci.yml`.

---

## 5. Auth contract (all clients)

- Access token (JWT, ~15 min) is sent as `Authorization: Bearer <token>`; refresh token (~30 days) rotates on every `/auth/refresh` (reuse detection revokes the family).
- Token responses carry `expires_in` (access, seconds) **and** `refresh_expires_in` (refresh, seconds). Cookie lifetimes must use `refresh_expires_in`.
- **Admin / Web (browser):** access token in memory only; refresh token in an **HttpOnly, SameSite=strict** cookie owned by the same-origin BFF routes (`/api/auth/login|register|totp|refresh|logout`). Never put tokens in `localStorage`.
- **Mobile:** tokens only via `expo-secure-store`.
- 2FA (TOTP): login may return `{requires_2fa, mfa_token}`; complete via `/auth/totp/verify`. Allows recovery codes. Never bypass on admin logins.
- Admin endpoints gate on permissions (`require_permission`), not roles. Backend returns `403 FORBIDDEN` for insufficient access.

---

## 6. Payments contract (all clients)

- Checkout creates a PENDING payment; **only a verified webhook** may mark it SUCCESS and trigger subscription activation / verification review.
- The mock provider (dev/demo) requires the `x-mock-webhook-secret` header matching `PAYMENT_WEBHOOK_SECRET`; production validates this at boot (`backend/AGENTS.md` §15).
- Clients never send amounts, statuses, or provider ids that the server trusts — pricing is resolved server-side from `app_config`.

---

## 7. When working in each app

- **Backend:** follow `backend/AGENTS.md` end-to-end (layering, patterns, tests, migrations). Run all four validation commands before reporting.
- **Admin/Web:** pure API clients. Add types mirroring backend schemas, go through the shared client (`lib/api/client.ts` in admin, `lib/api.ts` in web), handle loading/empty/error states, never call `fetch` to the API from components. Use the BFF routes for anything touching tokens.
- **Mobile:** follow `mobile/AGENTS.md`; reuse design-system components, TanStack Query for server state, `useRemoteConfig()` for branding/copy.

---

## 8. Documentation map

| Topic | Location |
| --- | --- |
| Backend architecture (ERD, enums, indexes, endpoints) | `backend/docs/architecture.md` |
| Admin dashboard architecture + deployment | `backend/docs/admin-dashboard.md` |
| Backend conventions, invariants, pitfalls | `backend/AGENTS.md` |
| Mobile conventions | `mobile/AGENTS.md` |

When behavior changes materially, update the relevant doc and tests in the same change. Documentation must never contradict implementation.
