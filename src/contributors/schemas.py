from pydantic import BaseModel


class ContributorProfile(BaseModel):
    login: str
    avatar_url: str | None = None
    html_url: str | None = None
    name: str | None = None
    total_commits: int = 0
    total_prs: int = 0
    total_issues: int = 0
    total_reviews: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    repos: list[str] = []
    avg_commits_per_week: float = 0.0
    avg_pr_merge_time_hours: float | None = None


class ContributorRanking(BaseModel):
    login: str
    avatar_url: str | None = None
    score: float = 0.0
    rank: int = 0
    metric_value: float = 0.0
    metric_name: str = "commits"


class ContributorActivity(BaseModel):
    login: str
    date: str
    commits: int = 0
    prs_opened: int = 0
    prs_merged: int = 0
    reviews: int = 0


class ReviewMetrics(BaseModel):
    login: str
    reviews_given: int = 0
    review_comments: int = 0
    avg_review_turnaround_hours: float | None = None
