from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from enum import Enum
from typing import Optional

from src.config import Settings, get_settings
from src.auth.dependencies import require_repo_access
from src.models.user import User
from src.github.client import GitHubClient
from src.reports import (
    ActivityReportService,
    QualityReportService,
    ReleaseReportService,
    ActivityReport,
    QualityReport,
    ReleaseReport,
    ReportPeriod,
    OrgSummary,
)
from src.exports import PDFExporter, CSVExporter
from src.api.filters import DateRangeFilter, PaginationFilter, SortFilter
from datetime import datetime, timezone

router = APIRouter(prefix="/api/v1", tags=["reports"])


class ExportFormat(str, Enum):
    JSON = "json"
    PDF = "pdf"
    CSV = "csv"


def get_github_client(settings: Settings = Depends(get_settings)) -> GitHubClient:
    return GitHubClient(token=settings.github_token, org=settings.github_org)


def get_repos(settings: Settings = Depends(get_settings)) -> list[str]:
    return settings.repo_list


# Organization endpoints
@router.get("/org", response_model=OrgSummary)
async def get_org_summary(client: GitHubClient = Depends(get_github_client)):
    """Get organization summary with repository stats."""
    await client.get_org()
    repos = await client.list_repos()

    languages: dict[str, int] = {}
    total_stars = 0
    total_forks = 0
    total_issues = 0
    private_count = 0
    public_count = 0

    for repo in repos:
        total_stars += repo.get("stargazers_count", 0)
        total_forks += repo.get("forks_count", 0)
        total_issues += repo.get("open_issues_count", 0)
        if repo.get("private"):
            private_count += 1
        else:
            public_count += 1
        if repo.get("language"):
            lang = repo["language"]
            languages[lang] = languages.get(lang, 0) + 1

    return OrgSummary(
        org_name=client.org,
        total_repos=len(repos),
        total_private_repos=private_count,
        total_public_repos=public_count,
        total_stars=total_stars,
        total_forks=total_forks,
        total_open_issues=total_issues,
        languages=languages,
        generated_at=datetime.now(timezone.utc),
    )


@router.get("/repos")
async def list_repos(
    language: Optional[str] = Query(None, description="Filter by language"),
    has_issues: Optional[bool] = Query(None, description="Filter by has issues"),
    archived: Optional[bool] = Query(None, description="Filter by archived status"),
    sort_by: Optional[str] = Query(
        None,
        description="Sort by: stars, forks, updated",
    ),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    pagination: PaginationFilter = Depends(),
    client: GitHubClient = Depends(get_github_client),
):
    """List all repositories in the organization with optional filters."""
    repos = await client.list_repos()

    results = []
    for r in repos:
        item = {
            "name": r["name"],
            "full_name": r["full_name"],
            "description": r.get("description"),
            "private": r["private"],
            "language": r.get("language"),
            "stars": r.get("stargazers_count", 0),
            "forks": r.get("forks_count", 0),
            "open_issues": r.get("open_issues_count", 0),
            "updated_at": r.get("updated_at"),
            "html_url": r["html_url"],
            "archived": r.get("archived", False),
        }

        # Apply filters
        if language and (r.get("language") or "").lower() != language.lower():
            continue
        if has_issues is not None:
            if has_issues and r.get("open_issues_count", 0) == 0:
                continue
            if not has_issues and r.get("open_issues_count", 0) > 0:
                continue
        if archived is not None and r.get("archived", False) != archived:
            continue

        results.append(item)

    # Sort
    sort_key_map = {
        "stars": "stars",
        "forks": "forks",
        "updated": "updated_at",
    }
    if sort_by and sort_by in sort_key_map:
        results.sort(
            key=lambda x: x.get(sort_key_map[sort_by]) or 0,
            reverse=(sort_order == "desc"),
        )

    # Paginate
    total = len(results)
    results = results[pagination.offset: pagination.offset + pagination.limit]

    return {"items": results, "total": total}


# Activity Report endpoints
@router.get("/reports/activity", response_model=ActivityReport)
async def get_activity_report(
    period: ReportPeriod = Query(ReportPeriod.MONTH, description="Report period"),
    repos: list[str] | None = Query(None, description="Specific repos to include"),
    date_range: DateRangeFilter = Depends(),
    client: GitHubClient = Depends(get_github_client),
    configured_repos: list[str] = Depends(get_repos),
):
    """Generate activity report for the organization with optional date range."""
    service = ActivityReportService(client)
    target_repos = repos or configured_repos or None
    return await service.generate_report(repos=target_repos, period=period)


@router.get("/reports/activity/export")
async def export_activity_report(
    format: ExportFormat = Query(ExportFormat.PDF, description="Export format"),
    period: ReportPeriod = Query(ReportPeriod.MONTH, description="Report period"),
    repos: list[str] | None = Query(None, description="Specific repos to include"),
    client: GitHubClient = Depends(get_github_client),
    configured_repos: list[str] = Depends(get_repos),
):
    """Export activity report in PDF or CSV format."""
    service = ActivityReportService(client)
    target_repos = repos or configured_repos or None
    report = await service.generate_report(repos=target_repos, period=period)

    if format == ExportFormat.PDF:
        exporter = PDFExporter()
        content = exporter.export_activity_report(report)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=activity-report-{report.period.value}.pdf"},
        )
    elif format == ExportFormat.CSV:
        exporter = CSVExporter()
        content = exporter.export_activity_report(report)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=activity-report-{report.period.value}.csv"},
        )
    else:
        return report


# Quality Report endpoints
@router.get("/reports/quality", response_model=QualityReport)
async def get_quality_report(
    repos: list[str] | None = Query(None, description="Specific repos to include"),
    client: GitHubClient = Depends(get_github_client),
    configured_repos: list[str] = Depends(get_repos),
):
    """Generate code quality report for the organization."""
    service = QualityReportService(client)
    target_repos = repos or configured_repos or None
    return await service.generate_report(repos=target_repos)


@router.get("/reports/quality/export")
async def export_quality_report(
    format: ExportFormat = Query(ExportFormat.PDF, description="Export format"),
    repos: list[str] | None = Query(None, description="Specific repos to include"),
    client: GitHubClient = Depends(get_github_client),
    configured_repos: list[str] = Depends(get_repos),
):
    """Export quality report in PDF or CSV format."""
    service = QualityReportService(client)
    target_repos = repos or configured_repos or None
    report = await service.generate_report(repos=target_repos)

    if format == ExportFormat.PDF:
        exporter = PDFExporter()
        content = exporter.export_quality_report(report)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=quality-report.pdf"},
        )
    elif format == ExportFormat.CSV:
        exporter = CSVExporter()
        content = exporter.export_quality_report(report)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=quality-report.csv"},
        )
    else:
        return report


# Release Report endpoints
@router.get("/reports/releases", response_model=ReleaseReport)
async def get_release_report(
    repos: list[str] | None = Query(None, description="Specific repos to include"),
    client: GitHubClient = Depends(get_github_client),
    configured_repos: list[str] = Depends(get_repos),
):
    """Generate release report for the organization."""
    service = ReleaseReportService(client)
    target_repos = repos or configured_repos or None
    return await service.generate_report(repos=target_repos)


@router.get("/reports/releases/export")
async def export_release_report(
    format: ExportFormat = Query(ExportFormat.PDF, description="Export format"),
    repos: list[str] | None = Query(None, description="Specific repos to include"),
    client: GitHubClient = Depends(get_github_client),
    configured_repos: list[str] = Depends(get_repos),
):
    """Export release report in PDF or CSV format."""
    service = ReleaseReportService(client)
    target_repos = repos or configured_repos or None
    report = await service.generate_report(repos=target_repos)

    if format == ExportFormat.PDF:
        exporter = PDFExporter()
        content = exporter.export_release_report(report)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=release-report.pdf"},
        )
    elif format == ExportFormat.CSV:
        exporter = CSVExporter()
        content = exporter.export_release_report(report)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=release-report.csv"},
        )
    else:
        return report


# Individual repo endpoints
@router.get("/repos/{repo_name}/commits")
async def get_repo_commits(
    repo_name: str,
    period: ReportPeriod = Query(ReportPeriod.MONTH, description="Time period"),
    client: GitHubClient = Depends(get_github_client),
    _user: User = Depends(require_repo_access()),
):
    """Get commits for a specific repository."""
    service = ActivityReportService(client)
    start, end = service._get_date_range(period)
    commits = await client.list_commits(repo_name, since=start, until=end)
    return {"repo": repo_name, "period": period.value, "count": len(commits), "commits": commits[:100]}


@router.get("/repos/{repo_name}/pulls")
async def get_repo_pulls(
    repo_name: str,
    state: str = Query("all", description="PR state: open, closed, all"),
    client: GitHubClient = Depends(get_github_client),
    _user: User = Depends(require_repo_access()),
):
    """Get pull requests for a specific repository."""
    prs = await client.list_pull_requests(repo_name, state=state)
    return {"repo": repo_name, "state": state, "count": len(prs), "pull_requests": prs[:100]}


@router.get("/repos/{repo_name}/issues")
async def get_repo_issues(
    repo_name: str,
    state: str = Query("all", description="Issue state: open, closed, all"),
    client: GitHubClient = Depends(get_github_client),
    _user: User = Depends(require_repo_access()),
):
    """Get issues for a specific repository."""
    issues = await client.list_issues(repo_name, state=state)
    return {"repo": repo_name, "state": state, "count": len(issues), "issues": issues[:100]}


@router.get("/repos/{repo_name}/releases")
async def get_repo_releases(
    repo_name: str,
    client: GitHubClient = Depends(get_github_client),
    _user: User = Depends(require_repo_access()),
):
    """Get releases for a specific repository."""
    releases = await client.list_releases(repo_name)
    return {"repo": repo_name, "count": len(releases), "releases": releases}


@router.get("/repos/{repo_name}/security")
async def get_repo_security(
    repo_name: str,
    client: GitHubClient = Depends(get_github_client),
    _user: User = Depends(require_repo_access()),
):
    """Get security alerts for a specific repository."""
    code_alerts = await client.list_code_scanning_alerts(repo_name)
    dependabot_alerts = await client.list_dependabot_alerts(repo_name)
    secret_alerts = await client.list_secret_scanning_alerts(repo_name)

    return {
        "repo": repo_name,
        "code_scanning": {"count": len(code_alerts), "alerts": code_alerts[:50]},
        "dependabot": {"count": len(dependabot_alerts), "alerts": dependabot_alerts[:50]},
        "secret_scanning": {"count": len(secret_alerts), "alerts": secret_alerts[:50]},
    }


@router.get("/repos/{repo_name}/workflows")
async def get_repo_workflows(
    repo_name: str,
    client: GitHubClient = Depends(get_github_client),
    _user: User = Depends(require_repo_access()),
):
    """Get GitHub Actions workflows for a specific repository."""
    workflows = await client.list_workflows(repo_name)
    runs = await client.list_workflow_runs(repo_name)

    return {
        "repo": repo_name,
        "workflows": workflows,
        "recent_runs": runs[:20],
    }
