# GAP - GitHub Analytics Platform

## Overview
GAP is a production-ready GitHub analytics platform with REST APIs, authentication, caching, webhooks, contributor analytics, trend analysis, scheduled reports, DORA metrics, and a React dashboard.

## Tech Stack
- **Backend**: Python 3.11+ / FastAPI / Uvicorn / SQLAlchemy async / Alembic
- **Frontend**: React 19 / TypeScript / Vite / Tailwind CSS v4 / React Query / Recharts
- **Database**: SQLite (dev) / PostgreSQL (prod) via SQLAlchemy async
- **Cache**: Redis (optional, graceful degradation)
- **Auth**: JWT + API keys (PBKDF2-SHA256 hashing, scoped permissions)
- **Rate Limiting**: slowapi (100/min default, 5/min register, 10/min login)
- **HTTP Client**: httpx (async)
- **PDF Export**: ReportLab
- **Logging**: Structured JSON to stdout
- **Linting**: Ruff (100 char line length)
- **Testing**: pytest + pytest-asyncio (backend), Vitest + RTL (frontend)
- **Deploy**: Docker (multi-stage), Render, GitHub Actions CI

## Project Structure
```
src/
  main.py              # FastAPI app with lifespan (DB, Redis, scheduler), all routers
  config.py            # Settings via pydantic-settings (model_config, not class Config)
  database.py          # SQLAlchemy async engine, session, Base
  cache.py             # Redis cache wrapper with graceful degradation
  middleware.py         # Rate limiter (slowapi) + request logging middleware
  logging_config.py    # Structured JSON logging setup
  models/              # SQLAlchemy models (8 tables)
  auth/                # JWT + API key auth (router, service, dependencies)
    dependencies.py    # get_current_user, require_permission(scope), require_admin
  api/router.py        # Core API routes (org, repos, reports, exports)
  github/client.py     # Async GitHub API client with pagination
  github/schemas.py    # GitHub data models
  reports/             # Activity, quality, release report services
  exports/             # PDF + CSV exporters
  webhooks/            # GitHub webhook receiver + signature verification
  contributors/        # Contributor analytics (profiles, rankings, activity)
  trends/              # Trend analysis (snapshots, comparisons, sparklines)
    collector.py       # Daily snapshot collection from GitHub API
  scheduler/           # Scheduled reports (CRUD, executor, email)
    background.py      # Async background scheduler loop (60s interval)
  teams/               # Team metrics + DORA (deploy freq, lead time, MTTR, CFR)
alembic/               # Database migrations
dashboard/             # React frontend (Vite + TypeScript + Tailwind)
  src/api/client.ts    # API client with typed endpoints
  src/components/      # Shared UI (Layout, Sidebar, StatCard, DataTable, ErrorBoundary, charts)
  src/pages/           # 10 pages (Login, Dashboard, Repos, Contributors, etc.)
  src/__tests__/       # Frontend tests (27 tests across 5 files)
tests/                 # Backend tests (64 tests across 10 files)
Dockerfile             # Multi-stage build (Python deps → Node build → runtime)
docker-compose.yml     # App + Postgres 16 + Redis 7
render.yaml            # Render deployment config
.github/workflows/     # CI: backend (ruff + pytest) + frontend (eslint + vitest + tsc)
```

## Setup & Running
```bash
cp .env.example .env   # Add your GITHUB_TOKEN and SECRET_KEY
pip install -e ".[dev]"
python -m src.main     # Backend at http://localhost:8000

# Dashboard
cd dashboard && npm install && npm run dev  # Frontend at http://localhost:5173

# Docker (includes Postgres + Redis)
docker compose up --build  # Full stack at http://localhost:8000
```

## API Endpoints
**Auth**: POST register, login, api-keys; GET me, api-keys; DELETE api-keys/{id}
**Org**: GET /org, /repos
**Reports**: GET /reports/activity, /quality, /releases + /export variants
**Repos**: GET /repos/{name}/commits, /pulls, /issues, /releases, /security, /workflows
**Contributors**: GET /contributors, /rankings, /export, /{username}, /{username}/activity
**Trends**: GET /trends/overview, /compare, /sparklines, /{metric}; POST /trends/collect (admin)
**Teams**: GET /teams/metrics, /dora, /compare, /export
**Webhooks**: POST /webhooks/github
**Schedules**: CRUD at /schedules + POST /{id}/run
**Health**: GET /health (deep check: DB + Redis connectivity, returns 503 if DB down)

## Testing
```bash
pytest tests/ -v                              # Backend: 64 tests (10 files)
cd dashboard && npx vitest run                # Frontend: 27 tests (5 files)
```

## Environment Variables
- `GITHUB_TOKEN` - GitHub PAT (required for live data)
- `GITHUB_ORG` - Organization (default: bhapi-inc)
- `DATABASE_URL` - Database (default: sqlite+aiosqlite:///./gap.db)
- `SECRET_KEY` - JWT signing key (change in production!)
- `REDIS_URL` - Redis cache (optional, degrades gracefully)
- `CORS_ORIGINS` - Comma-separated allowed origins (default: localhost:5173,localhost:8000)
- `GITHUB_WEBHOOK_SECRET` - Webhook HMAC secret (optional)
- `SMTP_HOST/PORT/USER/PASSWORD/FROM` - Email for scheduled reports (optional)
- `GITHUB_REPOS` - Comma-separated repo filter (optional, empty = all repos)

## Key Patterns
- Async throughout (SQLAlchemy async, httpx, aiosmtplib)
- Service layer: services handle business logic, routes handle HTTP
- Lazy DB engine initialization for testability
- Cache decorator pattern with graceful Redis degradation
- PBKDF2-SHA256 for password/API key hashing (no passlib dependency)
- Database auto-creates tables on startup (dev mode)
- Structured JSON logging to stdout (method, path, status, duration_ms)
- Rate limiting via slowapi with per-endpoint overrides
- API key scoped permissions (`permissions.scopes` array, `*` = full access)
- Background scheduler checks for due jobs every 60 seconds
- CORS locked to configured origins (no wildcard in production)
- ErrorBoundary wraps the React app for graceful crash recovery
- DataTable supports pagination (pageSize prop) and search (searchable prop)
