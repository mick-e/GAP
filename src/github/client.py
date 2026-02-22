import httpx
from datetime import datetime, timedelta
from typing import Any


class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(self, token: str, org: str):
        self.token = token
        self.org = org
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}{endpoint}"
            response = await client.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()

    async def _paginate(self, endpoint: str, params: dict | None = None) -> list[Any]:
        results = []
        params = params or {}
        params["per_page"] = 100
        page = 1

        async with httpx.AsyncClient() as client:
            while True:
                params["page"] = page
                url = f"{self.BASE_URL}{endpoint}"
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                if not data:
                    break
                results.extend(data)
                if len(data) < 100:
                    break
                page += 1

        return results

    # Organization & Repositories
    async def get_org(self) -> dict:
        return await self._request("GET", f"/orgs/{self.org}")

    async def list_repos(self) -> list[dict]:
        return await self._paginate(f"/orgs/{self.org}/repos")

    async def get_repo(self, repo: str) -> dict:
        return await self._request("GET", f"/repos/{self.org}/{repo}")

    # Commits
    async def list_commits(
        self, repo: str, since: datetime | None = None, until: datetime | None = None
    ) -> list[dict]:
        params = {}
        if since:
            params["since"] = since.isoformat()
        if until:
            params["until"] = until.isoformat()
        return await self._paginate(f"/repos/{self.org}/{repo}/commits", params)

    async def get_commit(self, repo: str, sha: str) -> dict:
        return await self._request("GET", f"/repos/{self.org}/{repo}/commits/{sha}")

    # Pull Requests
    async def list_pull_requests(
        self, repo: str, state: str = "all", since: datetime | None = None
    ) -> list[dict]:
        params = {"state": state, "sort": "updated", "direction": "desc"}
        prs = await self._paginate(f"/repos/{self.org}/{repo}/pulls", params)
        if since:
            prs = [pr for pr in prs if datetime.fromisoformat(pr["updated_at"].rstrip("Z")) >= since]
        return prs

    async def get_pull_request(self, repo: str, number: int) -> dict:
        return await self._request("GET", f"/repos/{self.org}/{repo}/pulls/{number}")

    # Issues
    async def list_issues(
        self, repo: str, state: str = "all", since: datetime | None = None
    ) -> list[dict]:
        params = {"state": state, "sort": "updated", "direction": "desc"}
        if since:
            params["since"] = since.isoformat()
        issues = await self._paginate(f"/repos/{self.org}/{repo}/issues", params)
        # Filter out pull requests (they appear in issues endpoint)
        return [i for i in issues if "pull_request" not in i]

    # Contributors
    async def list_contributors(self, repo: str) -> list[dict]:
        return await self._paginate(f"/repos/{self.org}/{repo}/contributors")

    # Releases
    async def list_releases(self, repo: str) -> list[dict]:
        return await self._paginate(f"/repos/{self.org}/{repo}/releases")

    async def get_latest_release(self, repo: str) -> dict | None:
        try:
            return await self._request("GET", f"/repos/{self.org}/{repo}/releases/latest")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    # Tags
    async def list_tags(self, repo: str) -> list[dict]:
        return await self._paginate(f"/repos/{self.org}/{repo}/tags")

    # Branches
    async def list_branches(self, repo: str) -> list[dict]:
        return await self._paginate(f"/repos/{self.org}/{repo}/branches")

    async def get_branch(self, repo: str, branch: str) -> dict:
        return await self._request("GET", f"/repos/{self.org}/{repo}/branches/{branch}")

    # Workflows (GitHub Actions)
    async def list_workflows(self, repo: str) -> list[dict]:
        data = await self._request("GET", f"/repos/{self.org}/{repo}/actions/workflows")
        return data.get("workflows", [])

    async def list_workflow_runs(
        self, repo: str, workflow_id: int | None = None, status: str | None = None
    ) -> list[dict]:
        endpoint = f"/repos/{self.org}/{repo}/actions/runs"
        params = {}
        if status:
            params["status"] = status
        data = await self._request("GET", endpoint, params=params)
        runs = data.get("workflow_runs", [])
        if workflow_id:
            runs = [r for r in runs if r["workflow_id"] == workflow_id]
        return runs

    # Code Scanning (Security)
    async def list_code_scanning_alerts(self, repo: str) -> list[dict]:
        try:
            return await self._paginate(f"/repos/{self.org}/{repo}/code-scanning/alerts")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []  # Code scanning not enabled
            raise

    async def list_dependabot_alerts(self, repo: str) -> list[dict]:
        try:
            return await self._paginate(f"/repos/{self.org}/{repo}/dependabot/alerts")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []  # Dependabot not enabled
            raise

    async def list_secret_scanning_alerts(self, repo: str) -> list[dict]:
        try:
            return await self._paginate(f"/repos/{self.org}/{repo}/secret-scanning/alerts")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []  # Secret scanning not enabled
            raise

    # Languages & Stats
    async def get_languages(self, repo: str) -> dict[str, int]:
        return await self._request("GET", f"/repos/{self.org}/{repo}/languages")

    async def get_commit_activity(self, repo: str) -> list[dict]:
        """Returns weekly commit activity for the last year"""
        try:
            return await self._request("GET", f"/repos/{self.org}/{repo}/stats/commit_activity")
        except httpx.HTTPStatusError:
            return []

    async def get_contributors_stats(self, repo: str) -> list[dict]:
        """Returns contributor commit activity"""
        try:
            return await self._request("GET", f"/repos/{self.org}/{repo}/stats/contributors")
        except httpx.HTTPStatusError:
            return []

    async def get_code_frequency(self, repo: str) -> list[list[int]]:
        """Returns weekly additions/deletions"""
        try:
            return await self._request("GET", f"/repos/{self.org}/{repo}/stats/code_frequency")
        except httpx.HTTPStatusError:
            return []
