import logging
from datetime import datetime, timezone
from collections import defaultdict

from src.github.client import GitHubClient
from .schemas import (
    QualityReport,
    RepoQualitySummary,
    WorkflowStats,
    SecurityStats,
)


logger = logging.getLogger(__name__)


class QualityReportService:
    def __init__(self, client: GitHubClient):
        self.client = client

    async def _get_workflow_stats(self, repo: str) -> list[WorkflowStats]:
        workflows = await self.client.list_workflows(repo)
        runs = await self.client.list_workflow_runs(repo)

        # Group runs by workflow
        workflow_runs: dict[int, list[dict]] = defaultdict(list)
        for run in runs:
            workflow_runs[run["workflow_id"]].append(run)

        stats = []
        for wf in workflows:
            wf_runs = workflow_runs.get(wf["id"], [])
            successful = sum(1 for r in wf_runs if r.get("conclusion") == "success")
            failed = sum(1 for r in wf_runs if r.get("conclusion") == "failure")
            total = len(wf_runs)

            stats.append(
                WorkflowStats(
                    workflow_name=wf["name"],
                    total_runs=total,
                    successful_runs=successful,
                    failed_runs=failed,
                    success_rate=successful / total * 100 if total > 0 else 0,
                )
            )

        return stats

    async def _get_security_stats(self, repo: str) -> SecurityStats:
        code_alerts = await self.client.list_code_scanning_alerts(repo)
        dependabot_alerts = await self.client.list_dependabot_alerts(repo)
        secret_alerts = await self.client.list_secret_scanning_alerts(repo)

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        # Process code scanning alerts
        for alert in code_alerts:
            rule = alert.get("rule", {})
            severity = rule.get("security_severity_level", "medium").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        # Process dependabot alerts
        for alert in dependabot_alerts:
            advisory = alert.get("security_advisory", {})
            severity = advisory.get("severity", "medium").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        # Secret scanning alerts are always high severity
        severity_counts["high"] += len(secret_alerts)

        return SecurityStats(
            code_scanning_alerts=len(code_alerts),
            dependabot_alerts=len(dependabot_alerts),
            secret_scanning_alerts=len(secret_alerts),
            critical_alerts=severity_counts["critical"],
            high_alerts=severity_counts["high"],
            medium_alerts=severity_counts["medium"],
            low_alerts=severity_counts["low"],
        )

    async def generate_report(self, repos: list[str] | None = None) -> QualityReport:
        # Get all repos if not specified
        if not repos:
            all_repos = await self.client.list_repos()
            repos = [r["name"] for r in all_repos]

        repo_summaries = []
        total_security = SecurityStats(
            code_scanning_alerts=0,
            dependabot_alerts=0,
            secret_scanning_alerts=0,
            critical_alerts=0,
            high_alerts=0,
            medium_alerts=0,
            low_alerts=0,
        )

        for repo_name in repos:
            try:
                repo_info = await self.client.get_repo(repo_name)
                workflows = await self._get_workflow_stats(repo_name)
                security = await self._get_security_stats(repo_name)
                languages = await self.client.get_languages(repo_name)

                summary = RepoQualitySummary(
                    repo_name=repo_name,
                    default_branch=repo_info["default_branch"],
                    workflows=workflows,
                    security=security,
                    languages=languages,
                )
                repo_summaries.append(summary)

                # Aggregate totals
                total_security.code_scanning_alerts += security.code_scanning_alerts
                total_security.dependabot_alerts += security.dependabot_alerts
                total_security.secret_scanning_alerts += security.secret_scanning_alerts
                total_security.critical_alerts += security.critical_alerts
                total_security.high_alerts += security.high_alerts
                total_security.medium_alerts += security.medium_alerts
                total_security.low_alerts += security.low_alerts

            except Exception as e:
                logger.error("Error processing repo %s: %s", repo_name, e)
                continue

        return QualityReport(
            org_name=self.client.org,
            generated_at=datetime.now(timezone.utc),
            repos=repo_summaries,
            totals=total_security,
        )
