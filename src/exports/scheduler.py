import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.scheduled_export import ScheduledExport

logger = logging.getLogger(__name__)

SCHEDULE_INTERVALS = {
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
    "monthly": timedelta(days=30),
}


async def create_export(
    db: AsyncSession,
    name: str,
    export_type: str,
    data_source: str,
    schedule: str,
    recipients: list[str],
    config: dict | None,
    user_id: str,
) -> ScheduledExport:
    interval = SCHEDULE_INTERVALS.get(schedule, timedelta(days=1))
    export = ScheduledExport(
        name=name,
        export_type=export_type,
        data_source=data_source,
        schedule=schedule,
        recipients=recipients,
        config=config or {},
        created_by=user_id,
        next_run_at=datetime.now(timezone.utc) + interval,
    )
    db.add(export)
    await db.commit()
    await db.refresh(export)
    return export


async def list_exports(db: AsyncSession, user_id: str) -> list[ScheduledExport]:
    result = await db.execute(
        select(ScheduledExport).where(ScheduledExport.created_by == user_id)
    )
    return list(result.scalars().all())


async def get_export(
    db: AsyncSession, export_id: str, user_id: str
) -> ScheduledExport | None:
    result = await db.execute(
        select(ScheduledExport).where(
            ScheduledExport.id == export_id,
            ScheduledExport.created_by == user_id,
        )
    )
    return result.scalar_one_or_none()


async def update_export(
    db: AsyncSession, export: ScheduledExport, **kwargs
) -> ScheduledExport:
    for key, value in kwargs.items():
        if hasattr(export, key):
            setattr(export, key, value)
    if "schedule" in kwargs:
        interval = SCHEDULE_INTERVALS.get(kwargs["schedule"], timedelta(days=1))
        export.next_run_at = datetime.now(timezone.utc) + interval
    await db.commit()
    await db.refresh(export)
    return export


async def delete_export(db: AsyncSession, export: ScheduledExport) -> None:
    await db.delete(export)
    await db.commit()


async def get_due_exports(db: AsyncSession) -> list[ScheduledExport]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ScheduledExport).where(
            ScheduledExport.is_active.is_(True),
            ScheduledExport.next_run_at <= now,
        )
    )
    return list(result.scalars().all())


async def execute_export(export: ScheduledExport, db: AsyncSession) -> bool:
    """Generate export and email to recipients."""
    from src.config import get_settings
    from src.github.client import GitHubClient
    from src.reports.activity import ActivityReportService
    from src.reports.quality import QualityReportService
    from src.reports.releases import ReleaseReportService
    from src.reports.schemas import ReportPeriod
    from src.exports import PDFExporter, CSVExporter
    from src.scheduler.email import send_report_email

    settings = get_settings()
    client = GitHubClient(token=settings.github_token, org=settings.github_org)
    repos = (export.config or {}).get("repos") or settings.repo_list or None
    period = ReportPeriod((export.config or {}).get("period", "month"))

    try:
        # Generate report based on data_source
        if export.data_source == "contributors":
            service = ActivityReportService(client)
            report = await service.generate_report(repos=repos, period=period)
            if export.export_type == "pdf":
                content = PDFExporter().export_activity_report(report)
                filename = f"contributors-{period.value}.pdf"
            else:
                content = CSVExporter().export_activity_report(report)
                filename = f"contributors-{period.value}.csv"
        elif export.data_source == "teams":
            service = QualityReportService(client)
            report = await service.generate_report(repos=repos)
            if export.export_type == "pdf":
                content = PDFExporter().export_quality_report(report)
                filename = "teams-quality.pdf"
            else:
                content = CSVExporter().export_quality_report(report)
                filename = "teams-quality.csv"
        elif export.data_source == "trends":
            service = ReleaseReportService(client)
            report = await service.generate_report(repos=repos)
            if export.export_type == "pdf":
                content = PDFExporter().export_release_report(report)
                filename = "trends-releases.pdf"
            else:
                content = CSVExporter().export_release_report(report)
                filename = "trends-releases.csv"
        else:
            logger.error(f"Unknown data source: {export.data_source}")
            return False

        if export.recipients:
            await send_report_email(
                to=export.recipients,
                subject=f"GAP Scheduled Export - {export.name}",
                body=f"<p>Your scheduled {export.data_source} export is attached.</p>",
                attachment=content if isinstance(content, bytes) else content.encode(),
                attachment_name=filename,
            )

        export.last_run_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(f"Executed scheduled export: {export.name}")
        return True

    except Exception as e:
        logger.error(f"Failed to execute export {export.name}: {e}")
        return False
