from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from .service import TrendService
from .schemas import TrendOverview, TrendData, TrendComparison, Sparkline

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


@router.get("/{metric}", response_model=list[TrendData])
async def get_metric_trend(
    metric: str,
    days: int = Query(30, ge=1, le=365),
    service: TrendService = Depends(get_trend_service),
):
    return await service.get_metric_trend(metric, days)
