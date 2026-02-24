from datetime import datetime, timedelta, timezone

from src.github.client import GitHubClient
from .schemas import ContributorProfile, ContributorRanking, ContributorActivity


class ContributorService:
    def __init__(self, client: GitHubClient):
        self.client = client

    async def get_all_contributors(self, repos: list[str] | None = None) -> list[ContributorProfile]:
        if not repos:
            all_repos = await self.client.list_repos()
            repos = [r["name"] for r in all_repos]

        contributors: dict[str, ContributorProfile] = {}

        for repo_name in repos:
            try:
                repo_contributors = await self.client.list_contributors(repo_name)
                for c in repo_contributors:
                    login = c["login"]
                    if login not in contributors:
                        contributors[login] = ContributorProfile(
                            login=login,
                            avatar_url=c.get("avatar_url"),
                            html_url=c.get("html_url"),
                        )
                    contributors[login].total_commits += c.get("contributions", 0)
                    if repo_name not in contributors[login].repos:
                        contributors[login].repos.append(repo_name)

                # Get PR stats
                prs = await self.client.list_pull_requests(repo_name, state="all")
                for pr in prs:
                    login = pr["user"]["login"]
                    if login in contributors:
                        contributors[login].total_prs += 1

            except Exception:
                continue

        return sorted(contributors.values(), key=lambda c: c.total_commits, reverse=True)

    async def get_contributor_profile(
        self, username: str, repos: list[str] | None = None
    ) -> ContributorProfile | None:
        all_contributors = await self.get_all_contributors(repos)
        for c in all_contributors:
            if c.login == username:
                return c
        return None

    async def get_contributor_activity(
        self, username: str, repos: list[str] | None = None, days: int = 30
    ) -> list[ContributorActivity]:
        if not repos:
            all_repos = await self.client.list_repos()
            repos = [r["name"] for r in all_repos]

        since = datetime.now(timezone.utc) - timedelta(days=days)
        daily: dict[str, ContributorActivity] = {}

        for repo_name in repos:
            try:
                commits = await self.client.list_commits(repo_name, since=since)
                for c in commits:
                    author = c.get("commit", {}).get("author", {})
                    if author.get("name") == username or c.get("author", {}).get("login") == username:
                        date_str = author.get("date", "")[:10]
                        if date_str not in daily:
                            daily[date_str] = ContributorActivity(
                                login=username, date=date_str
                            )
                        daily[date_str].commits += 1
            except Exception:
                continue

        return sorted(daily.values(), key=lambda a: a.date)

    async def get_rankings(
        self, metric: str = "commits", repos: list[str] | None = None, limit: int = 20
    ) -> list[ContributorRanking]:
        contributors = await self.get_all_contributors(repos)

        rankings = []
        for c in contributors:
            value = getattr(c, f"total_{metric}", c.total_commits)
            rankings.append(ContributorRanking(
                login=c.login,
                avatar_url=c.avatar_url,
                metric_value=float(value),
                metric_name=metric,
            ))

        rankings.sort(key=lambda r: r.metric_value, reverse=True)
        for i, r in enumerate(rankings):
            r.rank = i + 1
            r.score = r.metric_value

        return rankings[:limit]
