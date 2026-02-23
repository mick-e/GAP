import pytest
from datetime import date, timedelta

from src.models.snapshot import Snapshot
from src.trends.service import TrendService


async def test_overview_empty(db):
    service = TrendService(db)
    overview = await service.get_overview(days=30)
    assert overview.period == "30d"
    assert overview.velocity.current_value == 0


async def test_overview_with_data(db):
    today = date.today()
    for i in range(5):
        snap = Snapshot(
            snapshot_date=today - timedelta(days=i),
            snapshot_type="daily",
            commit_count=10,
            pr_count=2,
            contributors_count=3,
        )
        db.add(snap)
    await db.commit()

    service = TrendService(db)
    overview = await service.get_overview(days=30)
    assert overview.velocity.current_value > 0


async def test_metric_trend(db):
    today = date.today()
    for i in range(7):
        snap = Snapshot(
            snapshot_date=today - timedelta(days=i),
            snapshot_type="daily",
            commit_count=10 + i,
        )
        db.add(snap)
    await db.commit()

    service = TrendService(db)
    trend = await service.get_metric_trend("commit_count", days=30)
    assert len(trend) == 7


async def test_comparison(db):
    today = date.today()
    # Current period
    for i in range(10):
        db.add(Snapshot(
            snapshot_date=today - timedelta(days=i),
            snapshot_type="daily",
            commit_count=20,
        ))
    # Previous period
    for i in range(10, 20):
        db.add(Snapshot(
            snapshot_date=today - timedelta(days=i),
            snapshot_type="daily",
            commit_count=10,
        ))
    await db.commit()

    service = TrendService(db)
    comparison = await service.get_comparison("commit_count", 15, 15)
    assert comparison.current_value > comparison.previous_value
    assert comparison.direction == "up"


async def test_sparklines(db):
    today = date.today()
    for i in range(14):
        db.add(Snapshot(
            snapshot_date=today - timedelta(days=i),
            snapshot_type="daily",
            commit_count=5,
            pr_count=2,
            open_issues=1,
            security_alerts=0,
        ))
    await db.commit()

    service = TrendService(db)
    sparklines = await service.get_sparklines(14)
    assert len(sparklines) == 4
    assert all(s.metric in ["commit_count", "pr_count", "open_issues", "security_alerts"]
               for s in sparklines)
