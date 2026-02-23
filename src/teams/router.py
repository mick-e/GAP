from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from src.config import Settings, get_settings
from src.github.client import GitHubClient
from .service import TeamService
from .schemas import TeamMetricsResponse, DORAMetrics, TeamComparison

router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


def get_team_service(settings: Settings = Depends(get_settings)) -> TeamService:
    client = GitHubClient(token=settings.github_token, org=settings.github_org)
    return TeamService(client)


@router.get("/metrics", response_model=TeamMetricsResponse)
async def get_team_metrics(
    days: int = Query(30, ge=1, le=365),
    service: TeamService = Depends(get_team_service),
):
    return await service.get_org_metrics(days)


@router.get("/dora", response_model=DORAMetrics)
async def get_dora_metrics(
    days: int = Query(30, ge=1, le=365),
    service: TeamService = Depends(get_team_service),
):
    return await service.get_dora_metrics(days)


@router.get("/compare", response_model=list[TeamComparison])
async def compare_repos(
    days: int = Query(30, ge=1, le=365),
    service: TeamService = Depends(get_team_service),
):
    return await service.compare_repos(days)


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
