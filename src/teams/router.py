from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from src.config import Settings, get_settings
from src.github.client import GitHubClient
from src.api.filters import DateRangeFilter, SortFilter
from .service import TeamService
from .schemas import TeamMetricsResponse, DORAMetrics, TeamComparison

router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


def get_team_service(settings: Settings = Depends(get_settings)) -> TeamService:
    client = GitHubClient(token=settings.github_token, org=settings.github_org)
    return TeamService(client)


@router.get("/metrics", response_model=TeamMetricsResponse)
async def get_team_metrics(
    days: int = Query(30, ge=1, le=365),
    date_range: DateRangeFilter = Depends(),
    service: TeamService = Depends(get_team_service),
):
    """Get organization team metrics with optional date range."""
    return await service.get_org_metrics(days)


@router.get("/dora", response_model=DORAMetrics)
async def get_dora_metrics(
    days: int = Query(30, ge=1, le=365),
    date_range: DateRangeFilter = Depends(),
    service: TeamService = Depends(get_team_service),
):
    """Get DORA metrics with optional date range."""
    return await service.get_dora_metrics(days)


@router.get("/compare")
async def compare_repos(
    days: int = Query(30, ge=1, le=365),
    repo_name: Optional[str] = Query(None, description="Filter by repo name"),
    sort_by: Optional[str] = Query(
        None,
        description="Sort by: commits, prs, releases, contributors",
    ),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    date_range: DateRangeFilter = Depends(),
    service: TeamService = Depends(get_team_service),
):
    """Compare repos with optional filtering and sorting."""
    comparisons = await service.compare_repos(days)

    # Filter by repo name
    if repo_name:
        comparisons = [
            c for c in comparisons
            if repo_name.lower() in c.repo_name.lower()
        ]

    # Sort
    sort_field_map = {
        "commits": "commits",
        "prs": "prs",
        "releases": "releases",
        "contributors": "contributors",
    }
    if sort_by and sort_by in sort_field_map:
        comparisons.sort(
            key=lambda c: getattr(c, sort_field_map[sort_by], 0),
            reverse=(sort_order == "desc"),
        )

    return comparisons


@router.get("/export")
async def export_team_data(
    format: str = Query("csv"),
    days: int = Query(30, ge=1, le=365),
    service: TeamService = Depends(get_team_service),
):
    comparisons = await service.compare_repos(days)
    if format == "csv":
        import csv
        from io import StringIO
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Repo", "Commits", "PRs", "Releases", "Contributors",
            "Avg PR Merge (hrs)", "Deploy Freq", "DORA Rating"
        ])
        for c in comparisons:
            writer.writerow([
                c.repo_name, c.commits, c.prs, c.releases, c.contributors,
                c.avg_pr_merge_hours or "", c.dora.deployment_frequency, c.dora.rating,
            ])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=team-metrics.csv"},
        )
    return comparisons
