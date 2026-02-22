# BHAPI - GitHub Reports API

Generate comprehensive reports for GitHub organization repositories.

## Setup

```bash
cp .env.example .env
# Edit .env with your GITHUB_TOKEN
pip install -e .
python -m src.main
```

## API

- `GET /api/v1/org` - Organization summary
- `GET /api/v1/repos` - List repositories
- `GET /api/v1/reports/activity` - Activity report
- `GET /api/v1/reports/quality` - Code quality report
- `GET /api/v1/reports/releases` - Release report
