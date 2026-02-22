from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class ReportPeriod(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    ALL_TIME = "all_time"


# Activity Report Schemas
class CommitStats(BaseModel):
    total_commits: int
    total_additions: int
    total_deletions: int
    total_files_changed: int
    authors: dict[str, int]  # author -> commit count
    daily_commits: dict[str, int]  # date -> count


class PRStats(BaseModel):
    total_prs: int
    open_prs: int
    merged_prs: int
    closed_prs: int
    avg_merge_time_hours: float | None
    authors: dict[str, int]  # author -> PR count


class IssueStats(BaseModel):
    total_issues: int
    open_issues: int
    closed_issues: int
    avg_close_time_hours: float | None
    labels: dict[str, int]  # label -> count


class ContributorStats(BaseModel):
    login: str
    commits: int
    prs: int
    issues: int
    avatar_url: str


class RepoActivitySummary(BaseModel):
    repo_name: str
    commits: CommitStats
    pull_requests: PRStats
    issues: IssueStats
    top_contributors: list[ContributorStats]


class ActivityReport(BaseModel):
    org_name: str
    period: ReportPeriod
    start_date: datetime
    end_date: datetime
    generated_at: datetime
    repos: list[RepoActivitySummary]
    totals: dict[str, int]


# Quality Report Schemas
class WorkflowStats(BaseModel):
    workflow_name: str
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float


class SecurityStats(BaseModel):
    code_scanning_alerts: int
    dependabot_alerts: int
    secret_scanning_alerts: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    low_alerts: int


class RepoQualitySummary(BaseModel):
    repo_name: str
    default_branch: str
    workflows: list[WorkflowStats]
    security: SecurityStats
    languages: dict[str, int]


class QualityReport(BaseModel):
    org_name: str
    generated_at: datetime
    repos: list[RepoQualitySummary]
    totals: SecurityStats


# Release Report Schemas
class ReleaseInfo(BaseModel):
    tag_name: str
    name: str | None
    body: str | None
    prerelease: bool
    published_at: datetime | None
    author: str
    html_url: str


class RepoReleaseSummary(BaseModel):
    repo_name: str
    total_releases: int
    latest_release: ReleaseInfo | None
    releases: list[ReleaseInfo]
    tags_count: int


class ReleaseReport(BaseModel):
    org_name: str
    generated_at: datetime
    repos: list[RepoReleaseSummary]
    total_releases: int


# Organization Summary
class OrgSummary(BaseModel):
    org_name: str
    total_repos: int
    total_private_repos: int
    total_public_repos: int
    total_stars: int
    total_forks: int
    total_open_issues: int
    languages: dict[str, int]
    generated_at: datetime
