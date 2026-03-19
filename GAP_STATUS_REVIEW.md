# GAP Project (formerly BHAPI-AI) — Status Review

**Date**: 2026-03-18
**Repo**: [mick-e/bhapi-ai](https://github.com/mick-e/bhapi-ai)
**Local Path**: `C:\claude\bhapi`
**Version**: 0.2.0 (Production Hardened)
**Branch**: `master` (direct push workflow, clean working tree)

---

## 1. Project Overview

GitHub Analytics Platform for the `bhapi-inc` organization. Full-featured REST API + React dashboard providing:
- Organization & repository analytics
- Contributor profiles & rankings
- DORA metrics & team performance
- Trend analysis & historical snapshots
- Scheduled report generation (PDF/CSV)
- GitHub webhook processing

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy async, Alembic |
| Frontend | React 19, Vite 7, TypeScript 5.9, Tailwind CSS v4, Recharts 3 |
| Database | PostgreSQL 16 (prod), SQLite (dev/test) |
| Cache | Redis 7 (optional, graceful degradation) |
| Auth | JWT (HS256) + API keys (PBKDF2-SHA256 hashed) |
| CI/CD | GitHub Actions (ruff + pytest + eslint + vitest + tsc) |
| Deploy | Render (render.yaml), Docker multi-stage, docker-compose |

---

## 2. Codebase Metrics

| Metric | Count |
|--------|-------|
| Backend Python files | 57 |
| Frontend TS/TSX files | ~30 |
| Backend tests | 64 (12 files) |
| Frontend tests | 27 (5 files) |
| Database models | 8 |
| API routers | 7 |
| Frontend pages | 10 |
| Frontend components | 8 |
| Git commits | 5 |
| Alembic migrations | 1 (initial schema) |

---

## 3. Module Status (All Complete)

| Module | Path | Status | Notes |
|--------|------|--------|-------|
| Auth (JWT + API keys) | `src/auth/` | ✅ Complete | Register, login, API key CRUD, rate-limited |
| Core API (24 endpoints) | `src/api/router.py` | ✅ Complete | Org, repos, reports, exports |
| GitHub Client | `src/github/` | ✅ Complete | Async httpx, pagination, security alerts |
| Reports (Activity/Quality/Release) | `src/reports/` | ✅ Complete | PDF + CSV export via ReportLab + pandas |
| Contributors | `src/contributors/` | ✅ Complete | Rankings, profiles, activity history |
| Trends | `src/trends/` | ✅ Complete | Snapshots, comparisons, sparklines |
| Teams & DORA | `src/teams/` | ✅ Complete | Deploy freq, lead time, MTTR, CFR |
| Scheduler | `src/scheduler/` | ✅ Complete | APScheduler, CRUD, email delivery |
| Webhooks | `src/webhooks/` | ✅ Complete | HMAC-SHA256 verification, event storage |
| Caching | `src/cache.py` | ✅ Complete | Redis with graceful degradation |
| Middleware | `src/middleware.py` | ✅ Complete | Request logging (method, path, status, duration) |
| Database | `src/database.py` | ✅ Complete | Async SQLAlchemy, auto-create tables |

### Frontend Pages (All Complete)

| Page | Description |
|------|-------------|
| Login | Authentication form |
| Dashboard | Org overview with summary stats |
| Repos | Repository list |
| RepoDetail | Single repo analytics |
| Contributors | Contributor rankings |
| ContributorDetail | Individual contributor profile |
| Reports | Report generation + PDF/CSV export |
| Teams | Team metrics & DORA analysis |
| Trends | Historical trend analysis |
| Settings | User & API key management |

---

## 4. CI/CD — BROKEN ❌

### Current Failure (Run #23248783540)

**Root Cause**: Missing `email_validator` dependency

```
ModuleNotFoundError: No module named 'email_validator'
```

- **22 tests errored** during collection (couldn't run): auth, background, scheduler, security, webhooks
- **42 tests passed**: cache, database, contributors, teams, trends
- **Frontend**: ✅ All passing

**Fix Required**: Add `email-validator` to `pyproject.toml` dependencies.

### Recent CI History

| Date | Trigger | Result |
|------|---------|--------|
| 2026-03-18 | README update | ❌ FAIL (email_validator) |
| 2026-03-14 | Dependabot undici | ❌ FAIL |
| 2026-03-13 | Dependabot undici | ✅ PASS (one run) |
| 2026-03-01 | Dependabot minimatch | Mixed |
| 2026-02-24 | Production hardening | ❌ FAIL |

### GitHub Actions Deprecation Warning
Node.js 20 actions deprecated — must upgrade to v4 actions (Node.js 24) by June 2026.

---

## 5. Open Pull Requests (2 Dependabot)

| PR | Title | Opened | Status |
|----|-------|--------|--------|
| #2 | Bump undici from 7.22.0 to 7.24.1 in /dashboard | 2026-03-13 | Open |
| #1 | Bump minimatch in /dashboard | 2026-03-01 | Open |

**No manual PRs open. No open issues.**

---

## 6. Code Quality Assessment

| Check | Status |
|-------|--------|
| TODO/FIXME comments | ✅ Zero found |
| Commented-out code | ✅ None |
| Stub implementations | ✅ None |
| Disabled/skipped tests | ✅ 1 (intentional — optional fakeredis) |
| Dead code | ✅ None detected |
| Security patterns | ✅ Rate limiting, CORS, HMAC, hashed keys |
| Structured logging | ✅ JSON to stdout |
| Type hints | ✅ Pydantic models + annotations |
| Error handling | ✅ Consistent HTTP exceptions |

---

## 7. Deployment Status

### Render Configuration (`render.yaml`)
- **Service**: `bhapi` (web, Python 3.11.7 + Node 20)
- **Database**: Managed PostgreSQL (free tier)
- **Build**: `pip install -e ".[postgres]" && cd dashboard && npm ci && npm run build`
- **Start**: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
- **Manual env vars needed**: `GITHUB_TOKEN`, `CORS_ORIGINS`

### Docker
- Multi-stage Dockerfile (deps → frontend build → runtime)
- docker-compose: App + Postgres 16 + Redis 7 with health checks

---

## 8. Action Items (Prioritized)

### P0 — Critical (CI Broken)

1. **Fix missing `email_validator` dependency**
   - Add `email-validator>=2.0` to `pyproject.toml` `[project.dependencies]`
   - This will restore 22 failing test collections
   - Verify: `pip install -e ".[dev]" && pytest tests/ -v` → 64/64 pass

### P1 — Should Do (Maintenance)

2. **Merge Dependabot PRs**
   - PR #2: undici 7.22.0 → 7.24.1 (security patch)
   - PR #1: minimatch bump (security patch)
   - Review changelogs, merge if no breaking changes

3. **Upgrade GitHub Actions to Node.js 24**
   - Update `.github/workflows/ci.yml` action versions to v4
   - Deadline: June 2026

### P2 — Nice to Have (Feature Enhancements)

| # | Feature | Description |
|---|---------|-------------|
| 4 | Real-time notifications | WebSocket support for live updates |
| 5 | Audit logging | Track user actions (login, API key creation, report generation) |
| 6 | OAuth/SSO integration | GitHub OAuth login instead of email/password only |
| 7 | Per-repo permissions | Scope API keys to specific repositories |
| 8 | Webhook replay | Ability to replay failed/missed webhook events |
| 9 | Advanced filtering | Complex query builders for reports and analytics |
| 10 | Report scheduling templates | Pre-built schedules (daily standup, weekly digest) |
| 11 | Trend predictions | ML-based forecasting on historical data |
| 12 | Custom/composite metrics | User-defined metrics beyond built-in DORA |
| 13 | Export scheduling | Automated recurring exports (not just reports) |

---

## 9. Database Schema (8 Models)

| Model | Key Fields |
|-------|-----------|
| `users` | email, hashed_password, name, role, is_active |
| `api_keys` | hashed key, prefix, permissions JSON, user_id FK, expires_at |
| `reports` | type, period, title, data JSON, created_by FK |
| `snapshots` | repo_name, snapshot_type, commit/PR/issue/security counts, metrics JSON |
| `webhook_events` | event_type, action, repo_name, sender, payload JSON, processed flag |
| `scheduled_jobs` | name, report_type, schedule, recipients JSON, config JSON, is_active |
| `contributors` | username, repo_name, commit/PR/issue counts, first/last commit timestamps |
| `team_metrics` | team_name, repo_name, deploy_freq, lead_time, MTTR, CFR, snapshot_date |

---

## 10. Security Features

- PBKDF2-SHA256 password & API key hashing (no passlib)
- JWT tokens (HS256, configurable expiry)
- GitHub webhook HMAC-SHA256 signature verification
- API key scoped permissions (supports `*` wildcard)
- Rate limiting: 100/min default, 5/min register, 10/min login
- CORS locked to configured origins (no wildcards)
- Request logging middleware for observability

---

## Summary

**The GAP project is feature-complete and production-hardened at v0.2.0.** The codebase is clean with zero technical debt markers. The only critical issue is **CI is broken due to a missing `email_validator` dependency** — a one-line fix. Two Dependabot PRs await review. The project has no open GitHub issues and no WIP branches. Future development would focus on the P2 feature enhancements listed above.
