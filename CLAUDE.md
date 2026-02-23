# BHAPI - GitHub Analytics Platform

## Overview
BHAPI is a full-featured GitHub analytics platform with REST APIs, authentication, caching, webhooks, contributor analytics, trend analysis, scheduled reports, DORA metrics, and a React dashboard.

## Tech Stack
- **Backend**: Python 3.11+ / FastAPI / Uvicorn / SQLAlchemy async / Alembic
- **Frontend**: React 18 / TypeScript / Vite / Tailwind CSS / React Query / Recharts
- **Database**: SQLite (dev) / PostgreSQL (prod) via SQLAlchemy async
- **Cache**: Redis (optional, graceful degradation)
- **Auth**: JWT + API keys (PBKDF2-SHA256 hashing)
- **HTTP Client**: httpx (async)
- **PDF Export**: ReportLab
- **Linting**: Ruff (100 char line length)
- **Testing**: pytest + pytest-asyncio (backend), Vitest + RTL (frontend)

## Project Structure
```
src/
  main.py              # FastAPI app with lifespan, all routers
  config.py            # Settings (all env vars)
  database.py          # SQLAlchemy async engine, session, Base
  cache.py             # Redis cache wrapper with graceful degradation
  models/              # SQLAlchemy models (8 tables)
  auth/                # JWT + API key auth (router, service, dependencies)
  api/router.py        # Core API routes (org, repos, reports, exports)
  github/client.py     # Async GitHub API client with pagination
  github/schemas.py    # GitHub data models
  reports/             # Activity, quality, release report services
  exports/             # PDF + CSV exporters
  webhooks/            # GitHub webhook receiver + signature verification
  contributors/        # Contributor analytics (profiles, rankings, activity)
  trends/              # Trend analysis (snapshots, comparisons, sparklines)
  scheduler/           # Scheduled reports (CRUD, executor, email)
  teams/               # Team metrics + DORA (deploy freq, lead time, MTTR, CFR)
alembic/               # Database migrations
dashboard/             # React frontend (Vite + TypeScript + Tailwind)
  src/api/client.ts    # API client with typed endpoints
  src/components/      # Shared UI (Layout, Sidebar, StatCard, DataTable, charts)
  src/pages/           # 10 pages (Login, Dashboard, Repos, Contributors, etc.)
tests/                 # Backend tests (55 tests across 8 files)
```

## Setup & Running
```bash
cp .env.example .env   # Add your GITHUB_TOKEN
pip install -e ".[dev]"
python -m src.main     # Backend at http://localhost:8000

# Dashboard
cd dashboard && npm install && npm run dev  # Frontend at http://localhost:5173
```

## API Endpoints
**Auth**: POST register, login, api-keys; GET me, api-keys; DELETE api-keys/{id}
**Org**: GET /org, /repos
**Reports**: GET /reports/activity, /quality, /releases + /export variants
**Repos**: GET /repos/{name}/commits, /pulls, /issues, /releases, /security, /workflows
**Contributors**: GET /contributors, /rankings, /export, /{username}, /{username}/activity
**Trends**: GET /trends/overview, /compare, /sparklines, /{metric}
**Teams**: GET /teams/metrics, /dora, /compare, /export
**Webhooks**: POST /webhooks/github
**Schedules**: CRUD at /schedules + POST /{id}/run

## Testing
```bash
pytest tests/ -v                              # Backend: 55 tests
cd dashboard && npx vitest run                # Frontend: 10 tests
```

## Environment Variables
- `GITHUB_TOKEN` - GitHub PAT (required for live data)
- `GITHUB_ORG` - Organization (default: bhapi-inc)
- `DATABASE_URL` - Database (default: sqlite+aiosqlite:///./bhapi.db)
- `SECRET_KEY` - JWT signing key
- `REDIS_URL` - Redis cache (optional)
- `GITHUB_WEBHOOK_SECRET` - Webhook HMAC secret (optional)
- `SMTP_HOST/PORT/USER/PASSWORD/FROM` - Email for scheduled reports (optional)

## Key Patterns
- Async throughout (SQLAlchemy async, httpx, aiosmtplib)
- Service layer: services handle business logic, routes handle HTTP
- Lazy DB engine initialization for testability
- Cache decorator pattern with graceful Redis degradation
- PBKDF2-SHA256 for password/API key hashing (no passlib dependency)
- Database auto-creates tables on startup (dev mode)
