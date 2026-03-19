import pytest

from src.models.webhook_event import WebhookEvent
from src.models.user import User
from src.auth.service import hash_password, create_access_token


@pytest.fixture
async def admin_user(db):
    user = User(
        email="admin@example.com",
        hashed_password=hash_password("adminpassword123"),
        name="Admin User",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def admin_client(client, admin_user):
    token = create_access_token({"sub": admin_user.id})
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
async def sample_events(db):
    events = []
    for i, (etype, action, repo, sender, processed) in enumerate([
        ("push", None, "repo-a", "alice", True),
        ("pull_request", "opened", "repo-a", "bob", True),
        ("pull_request", "closed", "repo-b", "alice", False),
        ("issues", "opened", "repo-b", "charlie", True),
        ("release", "published", "repo-a", "bob", False),
    ]):
        event = WebhookEvent(
            event_type=etype,
            action=action,
            repo_name=repo,
            sender=sender,
            payload={"index": i, "repository": {"name": repo}},
            delivery_id=f"delivery-{i}",
            processed=processed,
        )
        db.add(event)
    await db.commit()
    # Reload to get IDs
    from sqlalchemy import select
    result = await db.execute(select(WebhookEvent))
    events = list(result.scalars().all())
    return events


async def test_list_events(admin_client, sample_events):
    resp = await admin_client.get("/api/v1/webhooks/events")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5


async def test_list_events_filter_event_type(admin_client, sample_events):
    resp = await admin_client.get("/api/v1/webhooks/events?event_type=pull_request")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(e["event_type"] == "pull_request" for e in data)


async def test_list_events_filter_repo_name(admin_client, sample_events):
    resp = await admin_client.get("/api/v1/webhooks/events?repo_name=repo-b")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(e["repo_name"] == "repo-b" for e in data)


async def test_list_events_filter_processed(admin_client, sample_events):
    resp = await admin_client.get("/api/v1/webhooks/events?processed=false")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(e["processed"] is False for e in data)


async def test_list_events_pagination(admin_client, sample_events):
    resp = await admin_client.get("/api/v1/webhooks/events?limit=2&offset=0")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = await admin_client.get("/api/v1/webhooks/events?limit=2&offset=4")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_get_event(admin_client, sample_events):
    event_id = sample_events[0].id
    resp = await admin_client.get(f"/api/v1/webhooks/events/{event_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == event_id
    assert "payload" in data


async def test_get_event_not_found(admin_client):
    resp = await admin_client.get("/api/v1/webhooks/events/nonexistent-id")
    assert resp.status_code == 404


async def test_replay_event(admin_client, sample_events):
    # Pick an event that was already processed
    event = sample_events[0]
    resp = await admin_client.post(f"/api/v1/webhooks/events/{event.id}/replay")
    assert resp.status_code == 200
    data = resp.json()
    assert data["event_id"] == event.id
    assert data["success"] is True


async def test_replay_event_not_found(admin_client):
    resp = await admin_client.post("/api/v1/webhooks/events/nonexistent-id/replay")
    assert resp.status_code == 404


async def test_batch_replay(admin_client, sample_events):
    ids = [sample_events[0].id, sample_events[1].id]
    resp = await admin_client.post(
        "/api/v1/webhooks/events/replay-batch",
        json={"event_ids": ids},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["successful"] == 2
    assert data["failed"] == 0
    assert len(data["results"]) == 2


async def test_batch_replay_with_invalid_id(admin_client, sample_events):
    ids = [sample_events[0].id, "nonexistent-id"]
    resp = await admin_client.post(
        "/api/v1/webhooks/events/replay-batch",
        json={"event_ids": ids},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["successful"] == 1
    assert data["failed"] == 1


async def test_admin_only_list_events(auth_client):
    resp = await auth_client.get("/api/v1/webhooks/events")
    assert resp.status_code == 403


async def test_admin_only_get_event(auth_client):
    resp = await auth_client.get("/api/v1/webhooks/events/some-id")
    assert resp.status_code == 403


async def test_admin_only_replay(auth_client):
    resp = await auth_client.post("/api/v1/webhooks/events/some-id/replay")
    assert resp.status_code == 403


async def test_admin_only_batch_replay(auth_client):
    resp = await auth_client.post(
        "/api/v1/webhooks/events/replay-batch",
        json={"event_ids": ["some-id"]},
    )
    assert resp.status_code == 403
