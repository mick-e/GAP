import logging
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.github.client import GitHubClient
from src.models.snapshot import Snapshot

logger = logging.getLogger(__name__)


async def collect_daily_snapshot(db: AsyncSession) -> list[Snapshot]:
    settings = get_settings()
    client = GitHubClient(token=settings.github_token, org=settings.github_org)
    today = date.today()
    snapshots = []

    repos = await client.list_repos()
    target_repos = settings.repo_list or [r["name"] for r in repos]

    for repo_name in target_repos:
        try:
            commits = await client.list_commits(repo_name)
            prs = await client.list_pull_requests(repo_name, state="all")
            issues = await client.list_issues(repo_name, state="all")
            contributors = await client.list_contributors(repo_name)

            code_alerts = await client.list_code_scanning_alerts(repo_name)
            dependabot_alerts = await client.list_dependabot_alerts(repo_name)
            secret_alerts = await client.list_secret_scanning_alerts(repo_name)
            total_alerts = len(code_alerts) + len(dependabot_alerts) + len(secret_alerts)

            open_issues = sum(1 for i in issues if i.get("state") == "open")
            closed_issues = sum(1 for i in issues if i.get("state") == "closed")

            snapshot = Snapshot(
                snapshot_date=today,
                repo_name=repo_name,
                snapshot_type="daily",
                commit_count=len(commits),
                pr_count=len(prs),
                open_issues=open_issues,
                closed_issues=closed_issues,
                security_alerts=total_alerts,
                contributors_count=len(contributors),
                metrics={
                    "stars": next(
                        (r.get("stargazers_count", 0) for r in repos if r["name"] == repo_name), 0
                    ),
                    "forks": next(
                        (r.get("forks_count", 0) for r in repos if r["name"] == repo_name), 0
                    ),
                },
            )
            db.add(snapshot)
            snapshots.append(snapshot)
            logger.info(f"Snapshot collected for {repo_name}")

        except Exception as e:
            logger.error(f"Error collecting snapshot for {repo_name}: {e}")
            continue

    await db.commit()
    logger.info(f"Daily snapshot complete: {len(snapshots)} repos")
    return snapshots
