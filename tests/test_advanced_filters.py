import pytest
from unittest.mock import AsyncMock

from src.api.router import get_github_client, get_repos
from src.contributors.router import get_contributor_service
from src.teams.router import get_team_service


@pytest.fixture
def mock_github(client):
    """Override the get_github_client dependency with a mock."""
    from src.main import app

    mock = AsyncMock()
    mock.org = "test-org"
    mock.list_repos.return_value = [
        {
            "name": "alpha",
            "full_name": "test-org/alpha",
            "description": "Alpha repo",
            "private": False,
            "language": "Python",
            "stargazers_count": 100,
            "forks_count": 20,
            "open_issues_count": 5,
            "updated_at": "2026-03-10T00:00:00Z",
            "html_url": "https://github.com/test-org/alpha",
            "archived": False,
        },
        {
            "name": "beta",
            "full_name": "test-org/beta",
            "description": "Beta repo",
            "private": True,
            "language": "TypeScript",
            "stargazers_count": 50,
            "forks_count": 10,
            "open_issues_count": 0,
            "updated_at": "2026-03-15T00:00:00Z",
            "html_url": "https://github.com/test-org/beta",
            "archived": False,
        },
        {
            "name": "gamma",
            "full_name": "test-org/gamma",
            "description": "Archived repo",
            "private": False,
            "language": "Python",
            "stargazers_count": 10,
            "forks_count": 2,
            "open_issues_count": 3,
            "updated_at": "2025-01-01T00:00:00Z",
            "html_url": "https://github.com/test-org/gamma",
            "archived": True,
        },
    ]

    app.dependency_overrides[get_github_client] = lambda: mock
    app.dependency_overrides[get_repos] = lambda: []
    yield mock
    app.dependency_overrides.pop(get_github_client, None)
    app.dependency_overrides.pop(get_repos, None)


# --- Repos filtering ---


async def test_repos_no_filter(client, mock_github):
    resp = await client.get("/api/v1/repos")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


async def test_repos_filter_by_language(client, mock_github):
    resp = await client.get("/api/v1/repos?language=Python")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert all(r["language"] == "Python" for r in data["items"])


async def test_repos_filter_by_has_issues(client, mock_github):
    resp = await client.get("/api/v1/repos?has_issues=true")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert all(r["open_issues"] > 0 for r in data["items"])


async def test_repos_filter_by_no_issues(client, mock_github):
    resp = await client.get("/api/v1/repos?has_issues=false")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "beta"


async def test_repos_filter_by_archived(client, mock_github):
    resp = await client.get("/api/v1/repos?archived=true")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "gamma"


async def test_repos_sort_by_stars(client, mock_github):
    resp = await client.get("/api/v1/repos?sort_by=stars&sort_order=asc")
    assert resp.status_code == 200
    data = resp.json()
    names = [r["name"] for r in data["items"]]
    assert names == ["gamma", "beta", "alpha"]


async def test_repos_sort_by_forks_desc(client, mock_github):
    resp = await client.get("/api/v1/repos?sort_by=forks&sort_order=desc")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"][0]["name"] == "alpha"


# --- Pagination ---


async def test_repos_pagination_limit(client, mock_github):
    resp = await client.get("/api/v1/repos?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3


async def test_repos_pagination_offset(client, mock_github):
    resp = await client.get("/api/v1/repos?limit=2&offset=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1


async def test_repos_pagination_beyond(client, mock_github):
    resp = await client.get("/api/v1/repos?limit=10&offset=100")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 0
    assert data["total"] == 3


# --- Combined filters ---


async def test_repos_combined_language_and_sort(client, mock_github):
    resp = await client.get(
        "/api/v1/repos?language=Python&sort_by=stars&sort_order=desc"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["items"][0]["name"] == "alpha"
    assert data["items"][1]["name"] == "gamma"


async def test_repos_combined_archived_and_pagination(client, mock_github):
    resp = await client.get("/api/v1/repos?archived=false&limit=1&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 1


# --- Invalid filter values ---


async def test_repos_invalid_sort_order(client, mock_github):
    resp = await client.get("/api/v1/repos?sort_order=invalid")
    assert resp.status_code == 422


async def test_repos_invalid_limit(client, mock_github):
    resp = await client.get("/api/v1/repos?limit=-1")
    assert resp.status_code == 422


async def test_repos_invalid_offset(client, mock_github):
    resp = await client.get("/api/v1/repos?offset=-5")
    assert resp.status_code == 422


async def test_repos_limit_too_large(client, mock_github):
    resp = await client.get("/api/v1/repos?limit=999")
    assert resp.status_code == 422


# --- Contributors filtering ---


@pytest.fixture
def mock_contributor_svc(client):
    from src.main import app
    from src.contributors.schemas import ContributorProfile

    service = AsyncMock()
    service.get_all_contributors.return_value = [
        ContributorProfile(
            login="alice", total_commits=100, total_prs=20,
            total_issues=5, total_reviews=30, repos=["repo1"],
        ),
        ContributorProfile(
            login="bob", total_commits=50, total_prs=40,
            total_issues=10, total_reviews=5, repos=["repo1", "repo2"],
        ),
        ContributorProfile(
            login="charlie", total_commits=10, total_prs=5,
            total_issues=2, total_reviews=1, repos=["repo2"],
        ),
    ]
    app.dependency_overrides[get_contributor_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_contributor_service, None)


async def test_contributors_min_commits(client, mock_contributor_svc):
    resp = await client.get("/api/v1/contributors?min_commits=50")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert all(c["total_commits"] >= 50 for c in data["items"])


async def test_contributors_sort_by_prs(client, mock_contributor_svc):
    resp = await client.get(
        "/api/v1/contributors?sort_by=prs&sort_order=desc"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"][0]["login"] == "bob"


async def test_contributors_pagination(client, mock_contributor_svc):
    resp = await client.get("/api/v1/contributors?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3


async def test_contributors_combined_filters(client, mock_contributor_svc):
    resp = await client.get(
        "/api/v1/contributors?min_commits=10&sort_by=commits&sort_order=asc&limit=2"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert data["items"][0]["login"] == "charlie"
    assert len(data["items"]) == 2


# --- Teams filtering ---


@pytest.fixture
def mock_team_svc(client):
    from src.main import app
    from src.teams.schemas import TeamComparison, DORAMetrics

    service = AsyncMock()
    service.compare_repos.return_value = [
        TeamComparison(
            repo_name="alpha", commits=200, prs=50,
            releases=10, contributors=5,
            dora=DORAMetrics(deployment_frequency=2.0, rating="high"),
        ),
        TeamComparison(
            repo_name="beta", commits=100, prs=80,
            releases=5, contributors=3,
            dora=DORAMetrics(deployment_frequency=1.0, rating="medium"),
        ),
        TeamComparison(
            repo_name="gamma", commits=50, prs=10,
            releases=1, contributors=2,
            dora=DORAMetrics(deployment_frequency=0.1, rating="low"),
        ),
    ]
    app.dependency_overrides[get_team_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_team_service, None)


async def test_teams_compare_no_filter(client, mock_team_svc):
    resp = await client.get("/api/v1/teams/compare")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


async def test_teams_compare_filter_by_name(client, mock_team_svc):
    resp = await client.get("/api/v1/teams/compare?repo_name=alpha")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["repo_name"] == "alpha"


async def test_teams_compare_sort_by_prs(client, mock_team_svc):
    resp = await client.get(
        "/api/v1/teams/compare?sort_by=prs&sort_order=desc"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["repo_name"] == "beta"


async def test_teams_compare_sort_by_commits_asc(client, mock_team_svc):
    resp = await client.get(
        "/api/v1/teams/compare?sort_by=commits&sort_order=asc"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["repo_name"] == "gamma"


async def test_teams_compare_invalid_sort_order(client, mock_team_svc):
    resp = await client.get("/api/v1/teams/compare?sort_order=random")
    assert resp.status_code == 422
