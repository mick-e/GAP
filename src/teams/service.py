from datetime import datetime, timedelta

from src.github.client import GitHubClient
from src.github.schemas import PullRequest
from .schemas import DORAMetrics, TeamMetricsResponse, TeamComparison


def _rate_dora(metrics: DORAMetrics) -> str:
    if metrics.deployment_frequency >= 7 and metrics.lead_time_hours < 24:
        return "elite"
    if metrics.deployment_frequency >= 1 and metrics.lead_time_hours < 168:
        return "high"
    if metrics.deployment_frequency >= 0.25:
        return "medium"
    return "low"


class TeamService:
    def __init__(self, client: GitHubClient):
        self.client = client

    async def get_org_metrics(self, days: int = 30) -> TeamMetricsResponse:
        repos = await self.client.list_repos()
        since = datetime.utcnow() - timedelta(days=days)

        total_commits = 0
        total_prs = 0
        total_releases = 0
        all_contributors = set()

        for repo in repos:
            name = repo["name"]
            try:
                commits = await self.client.list_commits(name, since=since)
                total_commits += len(commits)

                prs = await self.client.list_pull_requests(name, state="all", since=since)
                total_prs += len(prs)

                releases = await self.client.list_releases(name)
                recent_releases = [
                    r for r in releases
                    if r.get("published_at") and
                    datetime.fromisoformat(r["published_at"].rstrip("Z")) >= since
                ]
                total_releases += len(recent_releases)

                contributors = await self.client.list_contributors(name)
                for c in contributors:
                    all_contributors.add(c["login"])
            except Exception:
                continue

        weeks = max(days / 7, 1)
        dora = DORAMetrics(
            deployment_frequency=round(total_releases / weeks, 2),
        )
        dora.rating = _rate_dora(dora)

        return TeamMetricsResponse(
            org_name=self.client.org,
            total_commits=total_commits,
            total_prs=total_prs,
            total_releases=total_releases,
            contributors_count=len(all_contributors),
            repos_count=len(repos),
            dora=dora,
        )

    async def get_dora_metrics(self, days: int = 30) -> DORAMetrics:
        repos = await self.client.list_repos()
        since = datetime.utcnow() - timedelta(days=days)
        weeks = max(days / 7, 1)

        total_releases = 0
        lead_times = []
        recovery_times = []
        total_deployments = 0
        failed_deployments = 0

        for repo in repos:
            name = repo["name"]
            try:
                releases = await self.client.list_releases(name)
                recent = [
                    r for r in releases
                    if r.get("published_at") and
                    datetime.fromisoformat(r["published_at"].rstrip("Z")) >= since
                ]
                total_releases += len(recent)

                # Lead time: time from first commit to release
                for release in recent:
                    pub = datetime.fromisoformat(release["published_at"].rstrip("Z"))
                    tag = release.get("tag_name", "")
                    try:
                        commits = await self.client.list_commits(name, until=pub)
                        if commits:
                            first = commits[-1].get("commit", {}).get("author", {}).get("date")
                            if first:
                                first_dt = datetime.fromisoformat(first.rstrip("Z"))
                                lead_hours = (pub - first_dt).total_seconds() / 3600
                                if 0 < lead_hours < 8760:
                                    lead_times.append(lead_hours)
                    except Exception:
                        pass

                # MTTR: time from bug issue open to close
                issues = await self.client.list_issues(name, state="closed", since=since)
                for issue in issues:
                    labels = [l["name"].lower() for l in issue.get("labels", [])]
                    if any(t in labels for t in ["bug", "incident", "hotfix"]):
                        created = datetime.fromisoformat(issue["created_at"].rstrip("Z"))
                        closed = issue.get("closed_at")
                        if closed:
                            closed_dt = datetime.fromisoformat(closed.rstrip("Z"))
                            recovery = (closed_dt - created).total_seconds() / 3600
                            recovery_times.append(recovery)

                # Change failure rate from workflow runs
                runs = await self.client.list_workflow_runs(name)
                for run in runs:
                    created = datetime.fromisoformat(run["created_at"].rstrip("Z"))
                    if created >= since:
                        total_deployments += 1
                        if run.get("conclusion") == "failure":
                            failed_deployments += 1

            except Exception:
                continue

        dora = DORAMetrics(
            deployment_frequency=round(total_releases / weeks, 2),
            lead_time_hours=round(sum(lead_times) / len(lead_times), 1) if lead_times else 0.0,
            mttr_hours=round(
                sum(recovery_times) / len(recovery_times), 1
            ) if recovery_times else 0.0,
            change_failure_rate=round(
                failed_deployments / total_deployments * 100, 1
            ) if total_deployments > 0 else 0.0,
        )
        dora.rating = _rate_dora(dora)
        return dora

    async def compare_repos(self, days: int = 30) -> list[TeamComparison]:
        repos = await self.client.list_repos()
        since = datetime.utcnow() - timedelta(days=days)
        weeks = max(days / 7, 1)
        comparisons = []

        for repo in repos:
            name = repo["name"]
            try:
                commits = await self.client.list_commits(name, since=since)
                prs = await self.client.list_pull_requests(name, state="all", since=since)
                releases = await self.client.list_releases(name)
                recent_releases = [
                    r for r in releases
                    if r.get("published_at") and
                    datetime.fromisoformat(r["published_at"].rstrip("Z")) >= since
                ]
                contributors = await self.client.list_contributors(name)

                merge_times = []
                for pr in prs:
                    if pr.get("merged_at"):
                        created = datetime.fromisoformat(pr["created_at"].rstrip("Z"))
                        merged = datetime.fromisoformat(pr["merged_at"].rstrip("Z"))
                        merge_times.append((merged - created).total_seconds() / 3600)

                dora = DORAMetrics(
                    deployment_frequency=round(len(recent_releases) / weeks, 2),
                )
                dora.rating = _rate_dora(dora)

                comparisons.append(TeamComparison(
                    repo_name=name,
                    commits=len(commits),
                    prs=len(prs),
                    releases=len(recent_releases),
                    contributors=len(contributors),
                    avg_pr_merge_hours=round(
                        sum(merge_times) / len(merge_times), 1
                    ) if merge_times else None,
                    dora=dora,
                ))
            except Exception:
                continue

        return sorted(comparisons, key=lambda c: c.commits, reverse=True)
