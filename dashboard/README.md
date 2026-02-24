# BHAPI Dashboard

React frontend for the BHAPI GitHub Analytics Platform.

## Stack

- React 19 + TypeScript
- Vite (dev server + build)
- Tailwind CSS v4
- TanStack React Query v5
- React Router v7
- Recharts (charts + sparklines)
- Vitest + React Testing Library (tests)

## Setup

```bash
npm install
npm run dev      # http://localhost:5173 (proxies /api to localhost:8000)
npm run build    # Production build to dist/
```

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/login` | Login | Email/password auth + registration |
| `/` | Dashboard | Overview with stat cards, charts, sparklines |
| `/repos` | Repos | Searchable, sortable, paginated repo table |
| `/repos/:name` | RepoDetail | Commits, PRs, issues, releases, security |
| `/contributors` | Contributors | Searchable contributor cards grid |
| `/contributors/:username` | ContributorDetail | Profile + activity timeline |
| `/trends` | Trends | Trend charts + period comparisons |
| `/teams` | Teams | Team metrics + DORA performance ratings |
| `/reports` | Reports | Generate activity/quality/release reports |
| `/settings` | Settings | API key management |

## Components

- **DataTable** - Generic sortable table with pagination (`pageSize` prop) and search (`searchable` prop)
- **ErrorBoundary** - Catches render errors, shows reload UI
- **Layout** - Main layout with sidebar navigation + logout
- **Sidebar** - Navigation links for all pages
- **StatCard** - Metric display card with label/value
- **TrendChart** / **SparklineChart** - Recharts-based visualizations
- **PageLoader** - Loading spinner

## Testing

```bash
npx vitest run     # 27 tests across 5 files
```

Test files in `src/__tests__/`:
- `App.test.tsx` - Routing + auth redirect (3 tests)
- `DataTable.test.tsx` - Sorting, pagination, search (14 tests)
- `ErrorBoundary.test.tsx` - Error catching + reload (4 tests)
- `Layout.test.tsx` - Sidebar navigation links (2 tests)
- `StatCard.test.tsx` - Rendering (4 tests)
