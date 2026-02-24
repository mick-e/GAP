import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone

from src.teams.service import TeamService
from src.teams.schemas import DORAMetrics


@pytest.fixture
def mock_client():
    client = AsyncMock()
    client.org = "test-org"
    client.list_repos.return_value = [{"name": "repo1"}]
    client.list_commits.return_value = [
        {"sha": "abc", "commit": {"author": {"name": "alice", "date": "2025-01-10T12:00:00Z"}}},
        {"sha": "def", "commit": {"author": {"name": "bob", "date": "2025-01-11T12:00:00Z"}}},
    ]
    client.list_pull_requests.return_value = [
        {
            "user": {"login": "alice"}, "state": "closed",
            "created_at": "2025-01-10T00:00:00Z",
            "merged_at": "2025-01-11T12:00:00Z",
        },
    ]
    client.list_releases.return_value = [
        {
            "tag_name": "v1.0.0",
            "published_at": datetime.now(timezone.utc).isoformat() + "Z",
        },
    ]
    client.list_contributors.return_value = [
        {"login": "alice", "contributions": 50},
        {"login": "bob", "contributions": 30},
    ]
    client.list_issues.return_value = [
        {
            "labels": [{"name": "bug"}],
            "created_at": "2025-01-10T00:00:00Z",
            "closed_at": "2025-01-11T00:00:00Z",
            "state": "closed",
        },
    ]
    client.list_workflow_runs.return_value = [
        {"created_at": datetime.now(timezone.utc).isoformat() + "Z", "conclusion": "success"},
        {"created_at": datetime.now(timezone.utc).isoformat() + "Z", "conclusion": "failure"},
    ]
    return client


async def test_get_org_metrics(mock_client):
    service = TeamService(mock_client)
    metrics = await service.get_org_metrics(days=30)
    assert metrics.org_name == "test-org"
    assert metrics.total_commits == 2
    assert metrics.repos_count == 1
    assert metrics.dora is not None


async def test_get_dora_metrics(mock_client):
    service = TeamService(mock_client)
    dora = await service.get_dora_metrics(days=30)
    assert isinstance(dora, DORAMetrics)
    assert dora.deployment_frequency >= 0
    assert dora.rating in ("elite", "high", "medium", "low")


async def test_compare_repos(mock_client):
    service = TeamService(mock_client)
    comparisons = await service.compare_repos(days=30)
    assert len(comparisons) == 1
    assert comparisons[0].repo_name == "repo1"
    assert comparisons[0].commits == 2


async def test_dora_rating_elite():
    dora = DORAMetrics(deployment_frequency=10.0, lead_time_hours=12.0)
    from src.teams.service import _rate_dora
    assert _rate_dora(dora) == "elite"


async def test_dora_rating_low():
    dora = DORAMetrics(deployment_frequency=0.1, lead_time_hours=500.0)
    from src.teams.service import _rate_dora
    assert _rate_dora(dora) == "low"
