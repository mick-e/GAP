from datetime import date, datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.snapshot import Snapshot
from .schemas import (
    TrendData, TrendComparison, TrendOverview, Sparkline,
    TrendPrediction, MovingAveragePoint,
)
from .predictions import linear_regression, moving_average


def _direction(change: float) -> str:
    if change > 0:
        return "up"
    elif change < 0:
        return "down"
    return "flat"


def _pct(current: float, previous: float) -> float:
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round((current - previous) / previous * 100, 1)


class TrendService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(self, days: int = 30) -> TrendOverview:
        today = date.today()
        current_start = today - timedelta(days=days)
        previous_start = current_start - timedelta(days=days)

        current = await self._aggregate_snapshots(current_start, today)
        previous = await self._aggregate_snapshots(previous_start, current_start)

        velocity_curr = current.get("commit_count", 0) + current.get("pr_count", 0)
        velocity_prev = previous.get("commit_count", 0) + previous.get("pr_count", 0)
        quality_curr = max(0, 100 - current.get("security_alerts", 0))
        quality_prev = max(0, 100 - previous.get("security_alerts", 0))
        engagement_curr = current.get("contributors_count", 0)
        engagement_prev = previous.get("contributors_count", 0)

        return TrendOverview(
            period=f"{days}d",
            velocity=TrendComparison(
                metric="velocity",
                current_value=velocity_curr,
                previous_value=velocity_prev,
                change=velocity_curr - velocity_prev,
                change_percent=_pct(velocity_curr, velocity_prev),
                direction=_direction(velocity_curr - velocity_prev),
            ),
            quality=TrendComparison(
                metric="quality",
                current_value=quality_curr,
                previous_value=quality_prev,
                change=quality_curr - quality_prev,
                change_percent=_pct(quality_curr, quality_prev),
                direction=_direction(quality_curr - quality_prev),
            ),
            engagement=TrendComparison(
                metric="engagement",
                current_value=engagement_curr,
                previous_value=engagement_prev,
                change=engagement_curr - engagement_prev,
                change_percent=_pct(engagement_curr, engagement_prev),
                direction=_direction(engagement_curr - engagement_prev),
            ),
        )

    async def get_metric_trend(self, metric: str, days: int = 30) -> list[TrendData]:
        today = date.today()
        start = today - timedelta(days=days)
        column = getattr(Snapshot, metric, Snapshot.commit_count)

        result = await self.db.execute(
            select(Snapshot.snapshot_date, func.sum(column))
            .where(Snapshot.snapshot_date >= start)
            .group_by(Snapshot.snapshot_date)
            .order_by(Snapshot.snapshot_date)
        )

        return [
            TrendData(date=str(row[0]), value=float(row[1] or 0))
            for row in result.all()
        ]

    async def get_comparison(
        self, metric: str, period1_days: int = 30, period2_days: int = 30
    ) -> TrendComparison:
        today = date.today()
        p1_start = today - timedelta(days=period1_days)
        p2_start = p1_start - timedelta(days=period2_days)

        column = getattr(Snapshot, metric, Snapshot.commit_count)

        r1 = await self.db.execute(
            select(func.sum(column)).where(
                Snapshot.snapshot_date >= p1_start, Snapshot.snapshot_date < today
            )
        )
        r2 = await self.db.execute(
            select(func.sum(column)).where(
                Snapshot.snapshot_date >= p2_start, Snapshot.snapshot_date < p1_start
            )
        )

        curr = float(r1.scalar() or 0)
        prev = float(r2.scalar() or 0)

        return TrendComparison(
            metric=metric,
            current_value=curr,
            previous_value=prev,
            change=curr - prev,
            change_percent=_pct(curr, prev),
            direction=_direction(curr - prev),
        )

    async def get_sparklines(self, days: int = 14) -> list[Sparkline]:
        metrics = ["commit_count", "pr_count", "open_issues", "security_alerts"]
        sparklines = []

        for metric in metrics:
            data = await self.get_metric_trend(metric, days)
            values = [d.value for d in data]
            labels = [d.date for d in data]
            current = values[-1] if values else 0.0
            prev = values[0] if values else 0.0
            sparklines.append(Sparkline(
                metric=metric,
                data=values,
                labels=labels,
                current=current,
                change_percent=_pct(current, prev),
            ))

        return sparklines

    async def get_metric_predictions(
        self, metric: str, days: int = 90
    ) -> TrendPrediction:
        trend_data = await self.get_metric_trend(metric, days)
        data_points = [
            (datetime.fromisoformat(d.date), d.value) for d in trend_data
        ]
        result = linear_regression(data_points)
        return TrendPrediction(
            metric=metric,
            trend=result["trend"],
            slope=result.get("slope"),
            confidence=result.get("confidence"),
            predictions=result.get("predictions", []),
            historical=trend_data,
        )

    async def get_metric_moving_average(
        self, metric: str, days: int = 90, window: int = 7
    ) -> list[MovingAveragePoint]:
        trend_data = await self.get_metric_trend(metric, days)
        data_points = [
            (datetime.fromisoformat(d.date), d.value) for d in trend_data
        ]
        result = moving_average(data_points, window)
        return [
            MovingAveragePoint(
                date=r["date"], value=r["value"], raw_value=r["raw_value"]
            )
            for r in result
        ]

    async def _aggregate_snapshots(self, start: date, end: date) -> dict:
        result = await self.db.execute(
            select(
                func.sum(Snapshot.commit_count),
                func.sum(Snapshot.pr_count),
                func.sum(Snapshot.open_issues),
                func.sum(Snapshot.security_alerts),
                func.sum(Snapshot.contributors_count),
            ).where(Snapshot.snapshot_date >= start, Snapshot.snapshot_date < end)
        )
        row = result.one()
        return {
            "commit_count": float(row[0] or 0),
            "pr_count": float(row[1] or 0),
            "open_issues": float(row[2] or 0),
            "security_alerts": float(row[3] or 0),
            "contributors_count": float(row[4] or 0),
        }
