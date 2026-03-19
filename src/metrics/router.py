from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.user import User
from src.auth.dependencies import get_current_user
from .engine import ALLOWED_VARIABLES, FormulaError
from . import service
from .schemas import (
    CustomMetricCreate, CustomMetricUpdate, CustomMetricResponse,
    CustomMetricEvaluation, VariableInfo,
)

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@router.post("/custom", response_model=CustomMetricResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_metric(
    body: CustomMetricCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        metric = await service.create_metric(
            db, body.name, body.formula, user.id,
            description=body.description, is_public=body.is_public,
        )
    except FormulaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_response(metric)


@router.get("/custom", response_model=list[CustomMetricResponse])
async def list_custom_metrics(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    metrics = await service.list_metrics(db, user.id)
    return [_to_response(m) for m in metrics]


@router.get("/variables", response_model=list[VariableInfo])
async def list_variables():
    return [
        VariableInfo(name=name, description=service.VARIABLE_DESCRIPTIONS.get(name, ""))
        for name in sorted(ALLOWED_VARIABLES)
    ]


@router.get("/custom/{metric_id}", response_model=CustomMetricResponse)
async def get_custom_metric(
    metric_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    metric = await service.get_metric(db, metric_id, user.id)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return _to_response(metric)


@router.put("/custom/{metric_id}", response_model=CustomMetricResponse)
async def update_custom_metric(
    metric_id: str,
    body: CustomMetricUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    metric = await service.get_metric(db, metric_id, user.id)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    if metric.created_by != user.id:
        raise HTTPException(status_code=403, detail="Not the metric owner")
    try:
        updates = body.model_dump(exclude_none=True)
        metric = await service.update_metric(db, metric, **updates)
    except FormulaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_response(metric)


@router.delete("/custom/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_metric(
    metric_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    metric = await service.get_metric(db, metric_id, user.id)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    if metric.created_by != user.id:
        raise HTTPException(status_code=403, detail="Not the metric owner")
    await service.delete_metric(db, metric)


@router.post(
    "/custom/{metric_id}/evaluate", response_model=CustomMetricEvaluation
)
async def evaluate_custom_metric(
    metric_id: str,
    days: int = Query(30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    metric = await service.get_metric(db, metric_id, user.id)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    try:
        result = await service.evaluate_metric(db, metric, days)
    except FormulaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


def _to_response(metric) -> CustomMetricResponse:
    return CustomMetricResponse(
        id=metric.id,
        name=metric.name,
        description=metric.description,
        formula=metric.formula,
        is_public=metric.is_public,
        created_by=metric.created_by,
        created_at=metric.created_at.isoformat(),
    )
