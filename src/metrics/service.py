from datetime import date, timedelta

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.custom_metric import CustomMetric
from src.models.snapshot import Snapshot
from src.models.team_metrics import TeamMetrics
from .engine import ALLOWED_VARIABLES, evaluate_formula, validate_formula, FormulaError


VARIABLE_DESCRIPTIONS = {
    "commits": "Total commit count",
    "prs": "Total pull request count",
    "issues": "Total open issues",
    "releases": "Total releases",
    "stars": "Total stars (from snapshot metrics)",
    "forks": "Total forks (from snapshot metrics)",
    "deploy_frequency": "DORA: deployment frequency",
    "lead_time": "DORA: lead time in hours",
    "mttr": "DORA: mean time to recovery in hours",
    "cfr": "DORA: change failure rate (0-1)",
    "contributors": "Total contributor count",
    "active_contributors": "Active contributors in period",
}


async def create_metric(
    db: AsyncSession, name: str, formula: str, user_id: str,
    description: str | None = None, is_public: bool = False,
) -> CustomMetric:
    if not validate_formula(formula):
        raise FormulaError("Invalid formula")
    metric = CustomMetric(
        name=name,
        description=description,
        formula=formula,
        created_by=user_id,
        is_public=is_public,
    )
    db.add(metric)
    await db.commit()
    await db.refresh(metric)
    return metric


async def list_metrics(db: AsyncSession, user_id: str) -> list[CustomMetric]:
    result = await db.execute(
        select(CustomMetric).where(
            or_(CustomMetric.created_by == user_id, CustomMetric.is_public.is_(True))
        )
    )
    return list(result.scalars().all())


async def get_metric(
    db: AsyncSession, metric_id: str, user_id: str
) -> CustomMetric | None:
    result = await db.execute(
        select(CustomMetric).where(
            CustomMetric.id == metric_id,
            or_(CustomMetric.created_by == user_id, CustomMetric.is_public.is_(True)),
        )
    )
    return result.scalar_one_or_none()


async def update_metric(
    db: AsyncSession, metric: CustomMetric, **kwargs
) -> CustomMetric:
    if "formula" in kwargs and kwargs["formula"] is not None:
        if not validate_formula(kwargs["formula"]):
            raise FormulaError("Invalid formula")
    for key, value in kwargs.items():
        if hasattr(metric, key) and value is not None:
            setattr(metric, key, value)
    await db.commit()
    await db.refresh(metric)
    return metric


async def delete_metric(db: AsyncSession, metric: CustomMetric) -> None:
    await db.delete(metric)
    await db.commit()


async def evaluate_metric(
    db: AsyncSession, metric: CustomMetric, days: int = 30
) -> dict:
    """Evaluate a custom metric by fetching variable values from the database."""
    variables = await _fetch_variables(db, days)
    result = evaluate_formula(metric.formula, variables)
    return {
        "metric_id": metric.id,
        "metric_name": metric.name,
        "formula": metric.formula,
        "result": round(result, 4),
        "variables": variables,
    }


async def _fetch_variables(db: AsyncSession, days: int = 30) -> dict[str, float]:
    """Fetch current values for all allowed variables from the database."""
    today = date.today()
    start = today - timedelta(days=days)

    # Snapshot aggregates
    snap_result = await db.execute(
        select(
            func.sum(Snapshot.commit_count),
            func.sum(Snapshot.pr_count),
            func.sum(Snapshot.open_issues),
            func.sum(Snapshot.contributors_count),
        ).where(Snapshot.snapshot_date >= start)
    )
    snap_row = snap_result.one()

    # DORA metrics (latest entry)
    dora_result = await db.execute(
        select(TeamMetrics)
        .where(TeamMetrics.metrics_date >= start)
        .order_by(TeamMetrics.metrics_date.desc())
        .limit(1)
    )
    dora = dora_result.scalar_one_or_none()

    return {
        "commits": float(snap_row[0] or 0),
        "prs": float(snap_row[1] or 0),
        "issues": float(snap_row[2] or 0),
        "releases": float(dora.total_releases if dora else 0),
        "stars": 0.0,
        "forks": 0.0,
        "deploy_frequency": float(dora.deployment_frequency if dora else 0),
        "lead_time": float(dora.lead_time_hours if dora else 0),
        "mttr": float(dora.mttr_hours if dora else 0),
        "cfr": float(dora.change_failure_rate if dora else 0),
        "contributors": float(snap_row[3] or 0),
        "active_contributors": float(snap_row[3] or 0),
    }
