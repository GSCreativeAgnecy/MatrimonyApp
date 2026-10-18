# Ardhang Matrimony

A production matrimony/matchmaking platform, organized as a monorepo.

| App | Directory | Stack |
| --- | --- | --- |
| Backend API | `backend/` | FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Redis, ARQ, Alembic |
| Admin dashboard | `admin/` | Next.js 14 (staff UI, BFF auth) |
| End-user web | `web/` | Next.js 14 (discover, matches, chat, profile) |
| Mobile app | `mobile/` | Expo SDK 57 / React Native |

The backend is the single source of truth for auth, payments, privacy and business rules. Clients are pure API consumers.

---

## Quick start (Windows, no Docker)

```bat
run.cmd                # API :8000 + admin :3001 + web :3000 + mobile (Expo)
run.cmd --no-mobile    # skip the Expo dev server
run.cmd api|admin|web|mobile    # start a single app
```

The first run creates `backend/.venv`, installs dependencies and seeds a SQLite
database at `backend/dev.db` — no Docker, Postgres or Redis required.

- API: http://localhost:8000 (docs at `/docs`)
- Admin dashboard: http://localhost:3001
- Web client: http://localhost:3000

### Default admin credentials (local dev only)

`run.cmd` seeds a development `SUPER_ADMIN` so the admin dashboard is usable out of the box:

```
Email:    admin@example.com
Password: ChangeMe123!
```

These come from `DEV_ADMIN_EMAIL` / `DEV_ADMIN_PASSWORD`, which are only read by the
seed when both are set (`backend/app/seed.py`). The values above are injected by
`run.cmd` for local testing.

> **Never set `DEV_ADMIN_EMAIL` / `DEV_ADMIN_PASSWORD` in production.** For the Docker
> stack they are opt-in via `docker-compose.yml`; leave them unset on real deployments.

---

## Docker stack

```bash
cd backend
docker compose up --build
```

Starts `proxy` (nginx), `api`, `worker`, `admin`, `web`, `postgres` and `redis`.
Required production variables: `POSTGRES_PASSWORD`, `JWT_SECRET_KEY` (≥32 chars),
`PAYMENT_PROVIDER`, `PAYMENT_API_KEY`, `PAYMENT_WEBHOOK_SECRET` (see `backend/.env.example`).

---

## Commands & docs

| Topic | Where |
| --- | --- |
| Monorepo guide, contracts, per-app commands | `AGENTS.md` |
| Backend architecture, conventions, pitfalls | `backend/AGENTS.md` |
| Backend design doc (ERD, enums, endpoints) | `backend/docs/architecture.md` |
| Admin dashboard architecture + deployment | `backend/docs/admin-dashboard.md` |
| Mobile conventions | `mobile/AGENTS.md` |

Validation gates: `pytest`, `ruff check`, `mypy app` (backend); `tsc --noEmit` for
`admin` / `web` / `mobile`. CI runs all of them (`.github/workflows/ci.yml`).
