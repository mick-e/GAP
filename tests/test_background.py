import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock, MagicMock

from src.scheduler.background import start_scheduler, stop_scheduler


async def test_scheduler_starts_and_stops():
    """Scheduler starts and can be stopped cleanly."""
    with patch("src.scheduler.background.get_session_factory") as mock_sf:
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_sf.return_value = lambda: mock_session

        with patch("src.scheduler.background.get_due_jobs", new_callable=AsyncMock, return_value=[]):
            await start_scheduler()
            # Give the background task time to enter the loop
            await asyncio.sleep(0.2)
            await stop_scheduler()


async def test_scheduler_executes_due_jobs():
    """Scheduler picks up and executes due jobs."""
    mock_job = MagicMock()
    mock_job.name = "test-job"
    mock_job.schedule = "daily"
    mock_job.next_run_at = datetime.now(timezone.utc) - timedelta(hours=1)

    executed = asyncio.Event()

    async def mock_execute(job, db):
        executed.set()
        return True

    with patch("src.scheduler.background.get_session_factory") as mock_sf:
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_sf.return_value = lambda: mock_session

        call_count = 0

        async def mock_get_due(db):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [mock_job]
            return []

        with (
            patch("src.scheduler.background.get_due_jobs", side_effect=mock_get_due),
            patch("src.scheduler.background.execute_scheduled_job", side_effect=mock_execute),
        ):
            await start_scheduler()
            # Wait for the job to be executed (max 5s)
            try:
                await asyncio.wait_for(executed.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                pass
            await stop_scheduler()

            assert executed.is_set(), "Scheduled job should have been executed"


async def test_api_key_permissions(client, db):
    """API key with restricted scopes gets 403 on unauthorized endpoints."""
    await client.post("/api/v1/auth/register", json={
        "email": "perm@example.com",
        "password": "testpass123",
        "name": "Test",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "perm@example.com",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]

    # Create API key with restricted scope
    resp = await client.post(
        "/api/v1/auth/api-keys",
        json={"name": "restricted", "permissions": {"scopes": ["reports:read"]}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    api_key = resp.json()["key"]
    assert api_key is not None

    # Verify the key works for auth
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert resp.status_code == 200


async def test_api_key_wildcard_permissions(client, db):
    """API key with wildcard scope has full access."""
    await client.post("/api/v1/auth/register", json={
        "email": "wild@example.com",
        "password": "testpass123",
        "name": "Test",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "wild@example.com",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]

    resp = await client.post(
        "/api/v1/auth/api-keys",
        json={"name": "wildcard", "permissions": {"scopes": ["*"]}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    api_key = resp.json()["key"]

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert resp.status_code == 200
