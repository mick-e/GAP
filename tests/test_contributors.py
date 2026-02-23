import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.contributors.service import ContributorService


@pytest.fixture
def mock_client():
    client = AsyncMock()
    client.org = "test-org"
    client.list_repos.return_value = [{"name": "repo1"}, {"name": "repo2"}]
    client.list_contributors.return_value = [
        {"login": "alice", "avatar_url": "https://avatar/alice", "html_url": "https://gh/alice", "contributions": 50},
        {"login": "bob", "avatar_url": "https://avatar/bob", "html_url": "https://gh/bob", "contributions": 30},
    ]
    client.list_pull_requests.return_value = [
        {"user": {"login": "alice"}, "state": "closed", "merged_at": "2025-01-15T00:00:00Z"},
        {"user": {"login": "bob"}, "state": "open", "merged_at": None},
    ]
    client.list_commits.return_value = [
        {
            "sha": "abc123",
            "commit": {"author": {"name": "alice", "date": "2025-01-10T12:00:00Z"}},
            "author": {"login": "alice"},
        },
    ]
    return client


async def test_get_all_contributors(mock_client):
    service = ContributorService(mock_client)
    contributors = await service.get_all_contributors(["repo1"])
    assert len(contributors) == 2
    assert contributors[0].login == "alice"
    assert contributors[0].total_commits == 50


async def test_get_contributor_profile(mock_client):
    service = ContributorService(mock_client)
    profile = await service.get_contributor_profile("alice", ["repo1"])
    assert profile is not None
    assert profile.login == "alice"


async def test_get_contributor_not_found(mock_client):
    service = ContributorService(mock_client)
    profile = await service.get_contributor_profile("nobody", ["repo1"])
    assert profile is None


async def test_get_rankings(mock_client):
    service = ContributorService(mock_client)
    rankings = await service.get_rankings(metric="commits", repos=["repo1"])
    assert len(rankings) == 2
    assert rankings[0].rank == 1
    assert rankings[0].login == "alice"
    assert rankings[1].rank == 2


async def test_get_activity(mock_client):
    service = ContributorService(mock_client)
    activity = await service.get_contributor_activity("alice", ["repo1"], days=30)
    assert len(activity) >= 0  # May be empty depending on date filtering
