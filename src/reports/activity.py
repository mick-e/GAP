import logging
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from src.github.client import GitHubClient
from src.github.schemas import Commit, PullRequest, Issue
from .schemas import (
    ActivityReport,
    RepoActivitySummary,
    CommitStats,
    PRStats,
    IssueStats,
    ContributorStats,
    ReportPeriod,
)


logger = logging.getLogger(__name__)


class ActivityReportService:
    def __init__(self, client: GitHubClient):
        self.client = client

    def _get_date_range(self, period: ReportPeriod) -> tuple[datetime, datetime]:
        end = datetime.now(timezone.utc)
        if period == ReportPeriod.DAY:
            start = end - timedelta(days=1)
        elif period == ReportPeriod.WEEK:
            start = end - timedelta(weeks=1)
        elif period == ReportPeriod.MONTH:
            start = end - timedelta(days=30)
        elif period == ReportPeriod.QUARTER:
            start = end - timedelta(days=90)
        elif period == ReportPeriod.YEAR:
            start = end - timedelta(days=365)
        else:  # ALL_TIME
            start = datetime(2000, 1, 1)
        return start, end

    async def _get_commit_stats(
        self, repo: str, since: datetime, until: datetime
    ) -> CommitStats:
        commits_data = await self.client.list_commits(repo, since=since, until=until)

        authors: dict[str, int] = defaultdict(int)
        daily_commits: dict[str, int] = defaultdict(int)
        total_additions = 0
        total_deletions = 0
        total_files = 0

        for c in commits_data:
            commit = Commit.from_api(c)
            if commit.author_name:
                authors[commit.author_name] += 1
            if commit.author_date:
                day = commit.author_date.strftime("%Y-%m-%d")
                daily_commits[day] += 1
            total_additions += commit.additions
            total_deletions += commit.deletions
            total_files += commit.files_changed

        return CommitStats(
            total_commits=len(commits_data),
            total_additions=total_additions,
            total_deletions=total_deletions,
            total_files_changed=total_files,
            authors=dict(authors),
            daily_commits=dict(daily_commits),
        )

    async def _get_pr_stats(self, repo: str, since: datetime) -> PRStats:
        prs_data = await self.client.list_pull_requests(repo, state="all", since=since)

        authors: dict[str, int] = defaultdict(int)
        open_count = 0
        merged_count = 0
        closed_count = 0
        merge_times: list[float] = []

        for p in prs_data:
            pr = PullRequest.from_api(p)
            authors[pr.user_login] += 1

            if pr.state == "open":
                open_count += 1
            elif pr.merged_at:
                merged_count += 1
                # Calculate merge time
                merge_time = (pr.merged_at - pr.created_at).total_seconds() / 3600
                merge_times.append(merge_time)
            else:
                closed_count += 1

        avg_merge_time = sum(merge_times) / len(merge_times) if merge_times else None

        return PRStats(
            total_prs=len(prs_data),
            open_prs=open_count,
            merged_prs=merged_count,
            closed_prs=closed_count,
            avg_merge_time_hours=avg_merge_time,
            authors=dict(authors),
        )

    async def _get_issue_stats(self, repo: str, since: datetime) -> IssueStats:
        issues_data = await self.client.list_issues(repo, state="all", since=since)

        labels: dict[str, int] = defaultdict(int)
        open_count = 0
        closed_count = 0
        close_times: list[float] = []

        for i in issues_data:
            issue = Issue.from_api(i)

            for label in issue.labels:
                labels[label] += 1

            if issue.state == "open":
                open_count += 1
            else:
                closed_count += 1
                if issue.closed_at:
                    close_time = (issue.closed_at - issue.created_at).total_seconds() / 3600
                    close_times.append(close_time)

        avg_close_time = sum(close_times) / len(close_times) if close_times else None

        return IssueStats(
            total_issues=len(issues_data),
            open_issues=open_count,
            closed_issues=closed_count,
            avg_close_time_hours=avg_close_time,
            labels=dict(labels),
        )

    async def _get_top_contributors(
        self, repo: str, commit_stats: CommitStats, pr_stats: PRStats
    ) -> list[ContributorStats]:
        contributors_data = await self.client.list_contributors(repo)

        contributors = []
        for c in contributors_data[:10]:  # Top 10
            contributors.append(
                ContributorStats(
                    login=c["login"],
                    commits=commit_stats.authors.get(c["login"], c["contributions"]),
                    prs=pr_stats.authors.get(c["login"], 0),
                    issues=0,  # Would need additional API calls
                    avatar_url=c["avatar_url"],
                )
            )

        return contributors

    async def generate_report(
        self,
        repos: list[str] | None = None,
        period: ReportPeriod = ReportPeriod.MONTH,
    ) -> ActivityReport:
        start_date, end_date = self._get_date_range(period)

        # Get all repos if not specified
        if not repos:
            all_repos = await self.client.list_repos()
            repos = [r["name"] for r in all_repos]

        repo_summaries = []
        totals = {
            "total_commits": 0,
            "total_prs": 0,
            "total_issues": 0,
            "total_contributors": 0,
        }

        for repo_name in repos:
            try:
                commit_stats = await self._get_commit_stats(repo_name, start_date, end_date)
                pr_stats = await self._get_pr_stats(repo_name, start_date)
                issue_stats = await self._get_issue_stats(repo_name, start_date)
                top_contributors = await self._get_top_contributors(
                    repo_name, commit_stats, pr_stats
                )

                summary = RepoActivitySummary(
                    repo_name=repo_name,
                    commits=commit_stats,
                    pull_requests=pr_stats,
                    issues=issue_stats,
                    top_contributors=top_contributors,
                )
                repo_summaries.append(summary)

                totals["total_commits"] += commit_stats.total_commits
                totals["total_prs"] += pr_stats.total_prs
                totals["total_issues"] += issue_stats.total_issues
                totals["total_contributors"] += len(top_contributors)

            except Exception as e:
                # Log error but continue with other repos
                logger.error("Error processing repo %s: %s", repo_name, e)
                continue

        return ActivityReport(
            org_name=self.client.org,
            period=period,
            start_date=start_date,
            end_date=end_date,
            generated_at=datetime.now(timezone.utc),
            repos=repo_summaries,
            totals=totals,
        )
