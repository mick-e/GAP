from sqlalchemy import select

from src.models.user import User
from src.models.api_key import ApiKey
from src.models.report import Report
from src.models.snapshot import Snapshot
from src.models.webhook_event import WebhookEvent
from src.models.contributor import Contributor
from src.models.team_metrics import TeamMetrics


async def test_tables_created(db):
    """All tables should exist after setup."""
    result = await db.execute(select(User))
    assert result.all() == []


async def test_create_user(db):
    user = User(email="test@db.com", hashed_password="hashed", name="DB Test")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    assert user.id is not None
    assert user.email == "test@db.com"
    assert user.role == "user"
    assert user.is_active is True


async def test_create_api_key(db):
    user = User(email="key@db.com", hashed_password="hashed")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    key = ApiKey(name="test-key", hashed_key="hashed_key", prefix="bhapi_abcd", user_id=user.id)
    db.add(key)
    await db.commit()
    await db.refresh(key)

    assert key.id is not None
    assert key.user_id == user.id


async def test_create_report(db):
    user = User(email="report@db.com", hashed_password="hashed")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    report = Report(
        report_type="activity", title="Test Report", data={"test": True}, created_by=user.id
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    assert report.id is not None
    assert report.data == {"test": True}


async def test_create_snapshot(db):
    from datetime import date
    snap = Snapshot(
        snapshot_date=date.today(), snapshot_type="daily", commit_count=42, repo_name="test-repo"
    )
    db.add(snap)
    await db.commit()
    await db.refresh(snap)

    assert snap.id is not None
    assert snap.commit_count == 42


async def test_create_webhook_event(db):
    event = WebhookEvent(
        event_type="push", payload={"ref": "refs/heads/main"}, repo_name="test-repo"
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    assert event.id is not None
    assert event.processed is False


async def test_create_contributor(db):
    contrib = Contributor(login="testuser", total_commits=100, repos=["repo1", "repo2"])
    db.add(contrib)
    await db.commit()
    await db.refresh(contrib)

    assert contrib.id is not None
    assert contrib.total_commits == 100
    assert contrib.repos == ["repo1", "repo2"]


async def test_create_team_metrics(db):
    from datetime import date
    tm = TeamMetrics(
        metrics_date=date.today(),
        deployment_frequency=2.5,
        lead_time_hours=24.0,
        repo_name="test-repo",
    )
    db.add(tm)
    await db.commit()
    await db.refresh(tm)

    assert tm.id is not None
    assert tm.deployment_frequency == 2.5


async def test_user_cascade_delete(db):
    user = User(email="cascade@db.com", hashed_password="hashed")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    key = ApiKey(name="cascade-key", hashed_key="hashed_cascade", prefix="bhapi_csc", user_id=user.id)
    db.add(key)
    await db.commit()

    await db.delete(user)
    await db.commit()

    result = await db.execute(select(ApiKey).where(ApiKey.user_id == user.id))
    assert result.scalar_one_or_none() is None
