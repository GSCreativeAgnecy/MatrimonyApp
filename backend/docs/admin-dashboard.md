# Admin Dashboard

The **Matchmaking Admin** is a separate production-grade web application that
operates the matrimony platform. It is a Next.js (App Router) + TypeScript app
living in `admin/` and communicating exclusively with the FastAPI backend.

> **The dashboard never touches PostgreSQL.** The FastAPI API is the only source
> of truth and the only place business rules are enforced.

---

## 1. Architecture

```
React Native Mobile App          Admin Web Dashboard (Next.js)
        │                                │
        │  HTTPS                        │ HTTPS
        ▼                                ▼
     FastAPI API  ───────────────────────┘   (single, authoritative backend)
        │
        ├── PostgreSQL
        ├── Redis
        └── ARQ Workers
```

- **Frontend**: `admin/` — Next.js 14 (App Router), TypeScript (strict), Tailwind
  CSS, shadcn-style UI components, TanStack Query (server state), React Hook Form +
  Zod (forms), Recharts (charts), lucide-react (icons).
- **Backend**: existing FastAPI app extended with permission-based authorization,
  TOTP 2FA, and a full admin API surface (`/api/v1/admin/*`).

### Repository layout

```text
app/                    # FastAPI backend (authoritative)
admin/
├── app/                # Next.js App Router
│   ├── (app)/          # protected pages (sidebar shell)
│   ├── (auth)/login/   # sign-in (password + 2FA step)
│   └── api/auth/*      # BFF routes: login/totp/refresh/logout (HttpOnly cookie)
├── components/         # reusable UI + data-table, page-header, states, dialogs
├── lib/
│   ├── api/            # centralized API client + typed endpoint modules
│   ├── auth/           # auth context (in-memory access token)
│   ├── navigation.ts   # permission-filtered nav config
│   ├── types/          # API types (mirrors FastAPI schemas)
│   └── utils.ts
├── .env.example
├── next.config.mjs
├── package.json
└── tsconfig.json
```

---

## 2. Setup

### Backend (FastAPI)

```bash
# from repo root
python -m venv .venv && .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head          # applies the admin RBAC/2FA/campaigns migration
python -m app.seed            # seeds lookups, plans, app_config, role permissions
uvicorn app.main:app --reload # http://localhost:8000
```

The `admin` migration adds: `role_permissions`, `user_totp_secrets`,
`totp_recovery_codes`, `notification_campaigns`, new `UserRole` values
(`SUPPORT`, `FINANCE`, `ANALYST`), profile review columns, job-verification
`reviewer_notes`, and user suspension fields.

### Frontend (admin/)

```bash
cd admin
npm install
cp .env.example .env.local     # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                    # http://localhost:3001
```

### Development-only admin

Set both env vars and run `python -m app.seed` to create a SUPER_ADMIN
(`app/seed.py:_seed_dev_admin`):

```bash
DEV_ADMIN_EMAIL=admin@example.com
DEV_ADMIN_PASSWORD=ChangeMe123!
```

The password is never logged or committed and the account is only created when
both variables are present.

---

## 3. Environment variables

### `admin/.env.example`

| Variable | Purpose | Public? |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | FastAPI base URL | Yes — public values only |

Everything under `NEXT_PUBLIC_*` is shipped to the browser. **Never** put
`DATABASE_URL`, `JWT_SECRET_KEY`, `REDIS_URL`, `PAYMENT_API_KEY`,
`PAYMENT_WEBHOOK_SECRET`, S3 or SMTP credentials in public variables.

### Backend additions (`app/config/settings.py`)

| Setting | Purpose |
| --- | --- |
| `DEV_ADMIN_EMAIL` / `DEV_ADMIN_PASSWORD` | optional dev-only SUPER_ADMIN seed |
| `CORS_ORIGINS` | admin origin must be allowed (never `["*"]` in production) |

---

## 4. Authentication & sessions

- **Password login** → `POST /api/auth/login` (BFF) → backend `/auth/login`.
- **2FA (TOTP)** → when enabled, login returns `requires_2fa` + a 5-minute
  `mfa_token`; the client completes `POST /api/auth/totp` with a code or recovery
  code. No fake client-side 2FA.
- **Access token** stays in browser memory (never localStorage).
- **Refresh token** is stored by the Next.js BFF in an **HttpOnly, SameSite=Strict**
  cookie (`mm_admin_refresh`) and rotated on every `/api/auth/refresh` call.
- **Auto-refresh**: the API client refreshes once on a 401 and retries.
- **Logout** revokes the refresh token server-side and clears the cookie.
- Admins are the `User` table with role in
  `MODERATOR, VERIFIER, SUPPORT, FINANCE, ANALYST, ADMIN, SUPER_ADMIN`. A `USER`
  role is redirected away.

---

## 5. Roles & Permissions

Roles → permissions are defined in `app/security/permissions.py`, seeded into
`role_permissions`, and enforced by `require_permission` / `require_any_permission`.

| Permission | Enforced on |
| --- | --- |
| `users.read / update / suspend / ban / delete` | admin user list/detail/actions |
| `profiles.read / moderate`, `photos.moderate` | profile & photo moderation |
| `verification.*` | photo/account verification review |
| `job_verification.read / approve / reject` | job verification queue |
| `reports.read / resolve` | report queues & resolutions |
| `messages.read_private` | private conversation inspection (audited) |
| `payments.read / refund` | payment list & refunds |
| `subscriptions.read / manage` | subscriptions & plan CRUD |
| `notifications.send` | campaigns |
| `app_config.read / update` | remote config |
| `analytics.read` | analytics + dashboard |
| `audit_logs.read` | audit log viewer |
| `admin_users.read / manage` | admin user management + roles |

**The backend enforces all of these.** The frontend only hides controls.

---

## 6. Routes

| Route | Permission(s) | Description |
| --- | --- | --- |
| `/login` | public | sign in (password + 2FA) |
| `/dashboard` | any of analytics/users/reports read | KPI cards, action center, charts, recent activity |
| `/analytics` | analytics.read | users/engagement/matching/revenue/moderation |
| `/users`, `/users/[id]` | users.read | server-paginated table + detail with tabs & actions |
| `/profiles` | profiles.read | profile review queues |
| `/photos` | photos.moderate | photo approval queue |
| `/job-verifications` | job_verification.read | verification queue + approve/reject/info |
| `/reports` | reports.read | report queues + moderation actions |
| `/matches` | users.read/reports.read | match search |
| `/messages` | messages.read_private | audited conversation investigation |
| `/profile-shares` | profiles.read | shared profile records |
| `/payments` | payments.read | transactions + refunds (payments.refund) |
| `/subscriptions`, `/subscriptions/plans` | subscriptions.read | subscriptions + plan CRUD |
| `/notifications` | notifications.send | campaign builder |
| `/settings/app` | app_config.read | grouped remote config editing |
| `/audit-logs` | audit_logs.read | read-only audit trail |
| `/admin-users` | admin_users.read | admin account management |
| `/roles` | admin_users.read | role → permission editor |

Navigation in `lib/navigation.ts` is filtered by the logged-in admin's role.

---

## 7. API integration

- Central client: `lib/api/client.ts` (envelope parsing, error typing, auto-refresh).
- Typed endpoint modules: `lib/api/users.ts`, `lib/api/ops.ts`.
- Server state: TanStack Query with query keys per resource; mutations invalidate
  the relevant keys.
- Errors: backend `{ "error": { "code", "message" } }` is surfaced through
  `ApiClientError` and rendered by `ErrorState` (with retry) and toasts. No raw
  stack traces or internal details are shown.

### Type generation from OpenAPI

Types in `lib/types/` mirror the FastAPI schemas. A generated copy can be produced:

```bash
# with the API running
cd admin
npm run generate:types        # openapi-typescript http://localhost:8000/openapi.json -o lib/api/schema.ts
```

The hand-written types keep the app buildable without a live API and are the
reference for the UI.

---

## 8. Security considerations

- No secrets in the browser; no direct database access; no raw ORM leaks.
- Premium/subscription/payment/verification state is always derived server-side.
- Destructive actions require confirmation (destructive dialogs, typed phrases
  like `BAN`, `DELETE`, `REFUND`, `REJECT`).
- Private-message inspection requires `messages.read_private` and is audited
  (`admin.message_view`) with admin identity + IP/UA.
- Audit logs are read-only (no edit/delete endpoints).
- CSRF protection on the BFF: same-origin checks; the refresh cookie is
  SameSite=Strict and HttpOnly.
- Rate limiting, audit logging, and authorization all happen server-side.

---

## 9. Deployment

The admin app is independently deployable (e.g. `admin.example.com`):

```bash
cd admin
npm run build        # Next.js standalone output (.next/standalone)
npm run start -p 3001
```

- Point `NEXT_PUBLIC_API_URL` at the public API (e.g. `https://api.example.com`).
- Configure the backend `CORS_ORIGINS` to include the admin origin (never `*`).
- The refresh cookie requires HTTPS in production (`secure: true`).

### Docker Compose (API + dashboard together)

The root `docker-compose.yml` runs both the FastAPI stack and the admin dashboard
behind a single nginx reverse proxy:

```bash
docker compose up --build
```

- **No host ports are published.** Everything uses `expose`; a platform edge
  proxy (e.g. Coolify) routes a domain to the `proxy` service on port 80.
- Routing inside the nginx `proxy` (a single application origin):
  - `/` and `/_next/*` → `admin` (Next.js standalone, port 3001)
  - `/api/auth/*` → admin BFF (HttpOnly refresh cookie handling)
  - `/api/v1/*` → `api` (FastAPI, port 8000)
  - `postgres` (5432) and `redis` (6379) are never exposed outside the network.
- The admin image (`admin/Dockerfile`) builds with `NEXT_PUBLIC_API_URL=""` so the
  browser calls the same origin; the server-side BFF targets the API via the
  non-public `ADMIN_API_URL` (`http://api:8000`) environment variable.

---

## 10. Testing

Backend: new admin endpoints are covered by `tests/test_admin_*.py` plus
`tests/test_totp.py` (unauthenticated → 401, non-admin → 403, wrong permission →
403, authorized → 200, destructive actions, audit events, pagination/filters,
config cache invalidation already covered).

Frontend: `npm run typecheck` and `npm run build` validate types and the full
route set. Component-level tests can be added with Vitest/Testing Library in the
same pattern.
