from datetime import datetime

from src.github.client import GitHubClient
from src.github.schemas import Release
from .schemas import (
    ReleaseReport,
    RepoReleaseSummary,
    ReleaseInfo,
)


class ReleaseReportService:
    def __init__(self, client: GitHubClient):
        self.client = client

    def _to_release_info(self, release: Release) -> ReleaseInfo:
        return ReleaseInfo(
            tag_name=release.tag_name,
            name=release.name,
            body=release.body,
            prerelease=release.prerelease,
            published_at=release.published_at,
            author=release.author_login,
            html_url=release.html_url,
        )

    async def generate_report(self, repos: list[str] | None = None) -> ReleaseReport:
        # Get all repos if not specified
        if not repos:
            all_repos = await self.client.list_repos()
            repos = [r["name"] for r in all_repos]

        repo_summaries = []
        total_releases = 0

        for repo_name in repos:
            try:
                releases_data = await self.client.list_releases(repo_name)
                tags = await self.client.list_tags(repo_name)

                releases = [Release.from_api(r) for r in releases_data]
                release_infos = [self._to_release_info(r) for r in releases]

                latest = release_infos[0] if release_infos else None

                summary = RepoReleaseSummary(
                    repo_name=repo_name,
                    total_releases=len(releases),
                    latest_release=latest,
                    releases=release_infos,
                    tags_count=len(tags),
                )
                repo_summaries.append(summary)
                total_releases += len(releases)

            except Exception as e:
                print(f"Error processing repo {repo_name}: {e}")
                continue

        return ReleaseReport(
            org_name=self.client.org,
            generated_at=datetime.utcnow(),
            repos=repo_summaries,
            total_releases=total_releases,
        )
