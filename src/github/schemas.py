from pydantic import BaseModel
from datetime import datetime


class Repository(BaseModel):
    id: int
    name: str
    full_name: str
    description: str | None
    private: bool
    html_url: str
    default_branch: str
    language: str | None
    stargazers_count: int
    forks_count: int
    open_issues_count: int
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime | None


class Commit(BaseModel):
    sha: str
    message: str
    author_name: str | None
    author_email: str | None
    author_date: datetime | None
    committer_name: str | None
    committer_date: datetime | None
    additions: int = 0
    deletions: int = 0
    files_changed: int = 0

    @classmethod
    def from_api(cls, data: dict) -> "Commit":
        commit = data.get("commit", {})
        author = commit.get("author", {}) or {}
        committer = commit.get("committer", {}) or {}
        stats = data.get("stats", {})

        return cls(
            sha=data["sha"],
            message=commit.get("message", ""),
            author_name=author.get("name"),
            author_email=author.get("email"),
            author_date=datetime.fromisoformat(author["date"].rstrip("Z")) if author.get("date") else None,
            committer_name=committer.get("name"),
            committer_date=datetime.fromisoformat(committer["date"].rstrip("Z")) if committer.get("date") else None,
            additions=stats.get("additions", 0),
            deletions=stats.get("deletions", 0),
            files_changed=len(data.get("files", [])),
        )


class PullRequest(BaseModel):
    id: int
    number: int
    title: str
    state: str
    user_login: str
    created_at: datetime
    updated_at: datetime
    merged_at: datetime | None
    closed_at: datetime | None
    draft: bool
    additions: int
    deletions: int
    changed_files: int
    html_url: str

    @classmethod
    def from_api(cls, data: dict) -> "PullRequest":
        return cls(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            state=data["state"],
            user_login=data["user"]["login"],
            created_at=datetime.fromisoformat(data["created_at"].rstrip("Z")),
            updated_at=datetime.fromisoformat(data["updated_at"].rstrip("Z")),
            merged_at=datetime.fromisoformat(data["merged_at"].rstrip("Z")) if data.get("merged_at") else None,
            closed_at=datetime.fromisoformat(data["closed_at"].rstrip("Z")) if data.get("closed_at") else None,
            draft=data.get("draft", False),
            additions=data.get("additions", 0),
            deletions=data.get("deletions", 0),
            changed_files=data.get("changed_files", 0),
            html_url=data["html_url"],
        )


class Issue(BaseModel):
    id: int
    number: int
    title: str
    state: str
    user_login: str
    labels: list[str]
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    html_url: str

    @classmethod
    def from_api(cls, data: dict) -> "Issue":
        return cls(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            state=data["state"],
            user_login=data["user"]["login"],
            labels=[l["name"] for l in data.get("labels", [])],
            created_at=datetime.fromisoformat(data["created_at"].rstrip("Z")),
            updated_at=datetime.fromisoformat(data["updated_at"].rstrip("Z")),
            closed_at=datetime.fromisoformat(data["closed_at"].rstrip("Z")) if data.get("closed_at") else None,
            html_url=data["html_url"],
        )


class Contributor(BaseModel):
    login: str
    id: int
    avatar_url: str
    html_url: str
    contributions: int


class Release(BaseModel):
    id: int
    tag_name: str
    name: str | None
    body: str | None
    draft: bool
    prerelease: bool
    created_at: datetime
    published_at: datetime | None
    html_url: str
    author_login: str

    @classmethod
    def from_api(cls, data: dict) -> "Release":
        return cls(
            id=data["id"],
            tag_name=data["tag_name"],
            name=data.get("name"),
            body=data.get("body"),
            draft=data["draft"],
            prerelease=data["prerelease"],
            created_at=datetime.fromisoformat(data["created_at"].rstrip("Z")),
            published_at=datetime.fromisoformat(data["published_at"].rstrip("Z")) if data.get("published_at") else None,
            html_url=data["html_url"],
            author_login=data["author"]["login"],
        )


class WorkflowRun(BaseModel):
    id: int
    name: str
    status: str
    conclusion: str | None
    workflow_id: int
    run_number: int
    event: str
    created_at: datetime
    updated_at: datetime
    html_url: str

    @classmethod
    def from_api(cls, data: dict) -> "WorkflowRun":
        return cls(
            id=data["id"],
            name=data["name"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            workflow_id=data["workflow_id"],
            run_number=data["run_number"],
            event=data["event"],
            created_at=datetime.fromisoformat(data["created_at"].rstrip("Z")),
            updated_at=datetime.fromisoformat(data["updated_at"].rstrip("Z")),
            html_url=data["html_url"],
        )


class SecurityAlert(BaseModel):
    number: int
    state: str
    severity: str
    summary: str
    created_at: datetime
    html_url: str
    alert_type: str  # "code_scanning", "dependabot", "secret_scanning"

    @classmethod
    def from_code_scanning(cls, data: dict) -> "SecurityAlert":
        rule = data.get("rule", {})
        return cls(
            number=data["number"],
            state=data["state"],
            severity=rule.get("security_severity_level", "unknown"),
            summary=rule.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"].rstrip("Z")),
            html_url=data["html_url"],
            alert_type="code_scanning",
        )

    @classmethod
    def from_dependabot(cls, data: dict) -> "SecurityAlert":
        advisory = data.get("security_advisory", {})
        return cls(
            number=data["number"],
            state=data["state"],
            severity=advisory.get("severity", "unknown"),
            summary=advisory.get("summary", ""),
            created_at=datetime.fromisoformat(data["created_at"].rstrip("Z")),
            html_url=data["html_url"],
            alert_type="dependabot",
        )

    @classmethod
    def from_secret_scanning(cls, data: dict) -> "SecurityAlert":
        return cls(
            number=data["number"],
            state=data["state"],
            severity="high",  # Secret scanning alerts are always high severity
            summary=data.get("secret_type_display_name", "Secret detected"),
            created_at=datetime.fromisoformat(data["created_at"].rstrip("Z")),
            html_url=data["html_url"],
            alert_type="secret_scanning",
        )
