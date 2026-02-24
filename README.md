# BHAPI - GitHub Analytics Platform

Full-featured GitHub analytics platform with REST APIs, a React dashboard, and production deployment support. Track commits, PRs, issues, releases, contributors, DORA metrics, and more across your GitHub organization.

## Features

- **Organization Analytics** - Stars, forks, issues, languages across all repos
- **Activity Reports** - Commits, PRs, issues with daily breakdowns (PDF/CSV export)
- **Quality Reports** - CI workflows, security alerts (code scanning, Dependabot, secrets)
- **DORA Metrics** - Deployment frequency, lead time, MTTR, change failure rate
- **Contributor Profiles** - Per-user stats, activity timelines, rankings
- **Trend Analysis** - Daily snapshots, period comparisons, sparklines
- **Scheduled Reports** - Automated report generation with email delivery
- **GitHub Webhooks** - Real-time event processing with HMAC-SHA256 verification
- **React Dashboard** - 10-page SPA with charts, sortable/searchable tables, pagination

## Quick Start

```bash
# Backend
cp .env.example .env          # Add your GITHUB_TOKEN
pip install -e ".[dev]"
python -m src.main             # http://localhost:8000

# Dashboard
cd dashboard && npm install
npm run dev                    # http://localhost:5173

# Docker (full stack with Postgres + Redis)
docker compose up --build      # http://localhost:8000
```

## API

All endpoints under `/api/v1/`. Interactive docs at `/docs`.

| Group | Endpoints |
|-------|-----------|
| Auth | POST register, login, api-keys; GET me, api-keys; DELETE api-keys/{id} |
| Org | GET /org, /repos |
| Reports | GET /reports/activity, /quality, /releases + /export variants |
| Repos | GET /repos/{name}/commits, /pulls, /issues, /releases, /security, /workflows |
| Contributors | GET /contributors, /rankings, /{username}, /{username}/activity |
| Trends | GET /trends/overview, /compare, /sparklines, /{metric}; POST /trends/collect |
| Teams | GET /teams/metrics, /dora, /compare |
| Schedules | CRUD at /schedules + POST /{id}/run |
| Webhooks | POST /webhooks/github |
| Health | GET /health (DB + Redis connectivity check) |

## Security

- CORS locked to configured origins (no wildcards)
- Rate limiting: 100/min default, 5/min register, 10/min login
- API keys with scoped permissions (`*` = full access)
- PBKDF2-SHA256 password and API key hashing
- GitHub webhook HMAC-SHA256 signature verification

## Testing

```bash
pytest tests/ -v                    # 64 backend tests
cd dashboard && npx vitest run      # 27 frontend tests
```

## Deployment

- **Docker**: Multi-stage Dockerfile + docker-compose with Postgres 16 and Redis 7
- **Render**: `render.yaml` with web service + managed Postgres
- **CI**: GitHub Actions running ruff, pytest, eslint, vitest, and tsc

## Tech Stack

Python 3.11+ / FastAPI / SQLAlchemy async / Redis / React 19 / TypeScript / Vite / Tailwind CSS v4

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub Personal Access Token |
| `SECRET_KEY` | Yes (prod) | JWT signing key |
| `DATABASE_URL` | No | Default: SQLite |
| `REDIS_URL` | No | Optional cache |
| `CORS_ORIGINS` | No | Comma-separated allowed origins |
