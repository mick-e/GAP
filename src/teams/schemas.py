from pydantic import BaseModel


class DORAMetrics(BaseModel):
    deployment_frequency: float = 0.0
    deployment_frequency_unit: str = "per week"
    lead_time_hours: float = 0.0
    mttr_hours: float = 0.0
    change_failure_rate: float = 0.0
    rating: str = "low"  # elite, high, medium, low


class TeamMetricsResponse(BaseModel):
    org_name: str
    total_commits: int = 0
    total_prs: int = 0
    total_releases: int = 0
    contributors_count: int = 0
    repos_count: int = 0
    dora: DORAMetrics


class TeamComparison(BaseModel):
    repo_name: str
    commits: int = 0
    prs: int = 0
    releases: int = 0
    contributors: int = 0
    avg_pr_merge_hours: float | None = None
    dora: DORAMetrics
