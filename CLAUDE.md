# BHAPI - GitHub Reports API

## Overview
BHAPI is a GitHub analytics and reporting platform that generates comprehensive reports for GitHub organization repositories. It provides REST APIs for activity, quality, and release reporting with PDF/CSV export capabilities.

## Tech Stack
- **Backend**: Python 3.11+ / FastAPI 0.109+ / Uvicorn
- **HTTP Client**: httpx (async)
- **Config**: Pydantic Settings + python-dotenv
- **Data Processing**: pandas
- **PDF Export**: ReportLab
- **Linting**: Ruff (100 char line length)
- **Testing**: pytest + pytest-asyncio

## Project Structure
```
src/
  main.py              # FastAPI app entry point
  config.py            # Settings (GitHub token, org, host/port)
  api/router.py        # REST API routes
  github/client.py     # Async GitHub API client
  github/schemas.py    # GitHub data models (Repo, Commit, PR, Issue, etc.)
  reports/activity.py  # Activity report service (commits, PRs, issues)
  reports/quality.py   # Quality report service (workflows, security alerts)
  reports/releases.py  # Release report service
  reports/schemas.py   # Report data models
  exports/pdf.py       # PDF export (ReportLab)
  exports/csv.py       # CSV export
tests/                 # Unit tests
```

## Setup & Running
```bash
cp .env.example .env   # Add your GITHUB_TOKEN
pip install -e .
python -m src.main     # Or: uvicorn src.main:app --reload
```

## API Endpoints
- `GET /` - API info
- `GET /health` - Health check
- `GET /api/v1/org` - Organization summary
- `GET /api/v1/repos` - List repositories
- `GET /api/v1/reports/activity` - Activity report
- `GET /api/v1/reports/activity/export` - Export (JSON/PDF/CSV)
- `GET /api/v1/reports/quality` - Code quality report
- `GET /api/v1/reports/quality/export` - Export (JSON/PDF/CSV)
- `GET /api/v1/reports/releases` - Release report
- `GET /api/v1/reports/releases/export` - Export (JSON/PDF/CSV)
- `GET /api/v1/repos/{repo_name}/commits` - Commit history
- `GET /api/v1/repos/{repo_name}/pulls` - Pull requests
- `GET /api/v1/repos/{repo_name}/issues` - Issues
- `GET /api/v1/repos/{repo_name}/releases` - Releases
- `GET /api/v1/repos/{repo_name}/security` - Security alerts
- `GET /api/v1/repos/{repo_name}/workflows` - GitHub Actions workflows

## API Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing
```bash
pytest tests/ -v
```

## Environment Variables
- `GITHUB_TOKEN` - Required: GitHub Personal Access Token
- `GITHUB_ORG` - Organization to analyze (default: bhapi-inc)
- `GITHUB_REPOS` - Optional: comma-separated repo filter
- `API_HOST` - API host (default: 0.0.0.0)
- `API_PORT` - API port (default: 8000)
- `DEBUG` - Debug mode (default: false)

## Key Patterns
- All GitHub API calls are async (httpx.AsyncClient)
- Service layer pattern: services handle business logic, routes handle HTTP
- Pydantic models for all inputs/outputs
- GitHub client handles pagination automatically (100 items/page)
- Graceful error handling for disabled GitHub features (code scanning, Dependabot)

## Companion Repositories
The `github/` directory (gitignored) contains related repos from the bhapi-inc org:
- **back-office**: React 18 + TypeScript admin dashboard (Redux Toolkit)
- **bhapi-api**: Node.js/Express backend (Google Cloud, MongoDB, AWS)
- **bhapi-mobile**: React Native cross-platform mobile app
