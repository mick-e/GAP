from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from src.config import Settings, get_settings
from src.github.client import GitHubClient
from .service import ContributorService
from .schemas import ContributorProfile, ContributorRanking, ContributorActivity

router = APIRouter(prefix="/api/v1/contributors", tags=["contributors"])


def get_contributor_service(settings: Settings = Depends(get_settings)) -> ContributorService:
    client = GitHubClient(token=settings.github_token, org=settings.github_org)
    return ContributorService(client)


@router.get("", response_model=list[ContributorProfile])
async def list_contributors(
    repos: list[str] | None = Query(None),
    service: ContributorService = Depends(get_contributor_service),
):
    return await service.get_all_contributors(repos)


@router.get("/rankings", response_model=list[ContributorRanking])
async def get_rankings(
    metric: str = Query("commits", description="Metric to rank by"),
    limit: int = Query(20, ge=1, le=100),
    repos: list[str] | None = Query(None),
    service: ContributorService = Depends(get_contributor_service),
):
    return await service.get_rankings(metric=metric, repos=repos, limit=limit)


@router.get("/export")
async def export_contributors(
    format: str = Query("csv", description="Export format: csv or pdf"),
    repos: list[str] | None = Query(None),
    service: ContributorService = Depends(get_contributor_service),
):
    contributors = await service.get_all_contributors(repos)
    if format == "csv":
        import csv
        from io import StringIO
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Login", "Commits", "PRs", "Issues", "Reviews", "Repos"])
        for c in contributors:
            writer.writerow([c.login, c.total_commits, c.total_prs, c.total_issues,
                           c.total_reviews, ", ".join(c.repos)])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=contributors.csv"},
        )
    return contributors


@router.get("/{username}", response_model=ContributorProfile)
async def get_contributor(
    username: str,
    repos: list[str] | None = Query(None),
    service: ContributorService = Depends(get_contributor_service),
):
    profile = await service.get_contributor_profile(username, repos)
    if not profile:
        raise HTTPException(status_code=404, detail="Contributor not found")
    return profile


@router.get("/{username}/activity", response_model=list[ContributorActivity])
async def get_contributor_activity(
    username: str,
    days: int = Query(30, ge=1, le=365),
    repos: list[str] | None = Query(None),
    service: ContributorService = Depends(get_contributor_service),
):
    return await service.get_contributor_activity(username, repos, days)
