from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.auth.dependencies import require_admin
from .service import TrendService
from .collector import collect_daily_snapshot
from .schemas import (
    TrendOverview, TrendData, TrendComparison, Sparkline,
    TrendPrediction, MovingAveragePoint,
)

router = APIRouter(prefix="/api/v1/trends", tags=["trends"])


def get_trend_service(db: AsyncSession = Depends(get_db)) -> TrendService:
    return TrendService(db)


@router.get("/overview", response_model=TrendOverview)
async def get_trend_overview(
    days: int = Query(30, ge=1, le=365),
    service: TrendService = Depends(get_trend_service),
):
    return await service.get_overview(days)


@router.get("/compare", response_model=TrendComparison)
async def compare_periods(
    metric: str = Query("commit_count"),
    period1_days: int = Query(30, ge=1),
    period2_days: int = Query(30, ge=1),
    service: TrendService = Depends(get_trend_service),
):
    return await service.get_comparison(metric, period1_days, period2_days)


@router.get("/sparklines", response_model=list[Sparkline])
async def get_sparklines(
    days: int = Query(14, ge=1, le=90),
    service: TrendService = Depends(get_trend_service),
):
    return await service.get_sparklines(days)


@router.get("/predictions/{metric}", response_model=TrendPrediction)
async def get_predictions(
    metric: str,
    days: int = Query(90, ge=7, le=365),
    service: TrendService = Depends(get_trend_service),
):
    return await service.get_metric_predictions(metric, days)


@router.get("/moving-average/{metric}", response_model=list[MovingAveragePoint])
async def get_moving_average(
    metric: str,
    days: int = Query(90, ge=7, le=365),
    window: int = Query(7, ge=2, le=30),
    service: TrendService = Depends(get_trend_service),
):
    return await service.get_metric_moving_average(metric, days, window)


@router.post("/collect")
async def trigger_snapshot_collection(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    snapshots = await collect_daily_snapshot(db)
    return {"collected": len(snapshots), "repos": [s.repo_name for s in snapshots]}


@router.get("/{metric}", response_model=list[TrendData])
async def get_metric_trend(
    metric: str,
    days: int = Query(30, ge=1, le=365),
    service: TrendService = Depends(get_trend_service),
):
    return await service.get_metric_trend(metric, days)
