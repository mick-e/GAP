import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.github.client import GitHubClient
from src.reports.activity import ActivityReportService
from src.reports.quality import QualityReportService
from src.reports.releases import ReleaseReportService
from src.reports.schemas import ReportPeriod
from src.exports import PDFExporter
from src.models.scheduled_job import ScheduledJob
from .email import send_report_email

logger = logging.getLogger(__name__)


async def execute_scheduled_job(job: ScheduledJob, db: AsyncSession) -> bool:
    settings = get_settings()
    client = GitHubClient(token=settings.github_token, org=settings.github_org)
    repos = job.config.get("repos") or settings.repo_list or None
    period = ReportPeriod(job.config.get("period", "month"))

    try:
        if job.report_type == "activity":
            service = ActivityReportService(client)
            report = await service.generate_report(repos=repos, period=period)
            pdf = PDFExporter().export_activity_report(report)
            filename = f"activity-report-{period.value}.pdf"
        elif job.report_type == "quality":
            service = QualityReportService(client)
            report = await service.generate_report(repos=repos)
            pdf = PDFExporter().export_quality_report(report)
            filename = "quality-report.pdf"
        elif job.report_type == "releases":
            service = ReleaseReportService(client)
            report = await service.generate_report(repos=repos)
            pdf = PDFExporter().export_release_report(report)
            filename = "release-report.pdf"
        else:
            logger.error(f"Unknown report type: {job.report_type}")
            return False

        if job.recipients:
            await send_report_email(
                to=job.recipients,
                subject=f"GAP {job.report_type.title()} Report - {job.name}",
                body=f"<p>Your scheduled {job.report_type} report is attached.</p>",
                attachment=pdf,
                attachment_name=filename,
            )

        job.last_run_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(f"Executed scheduled job: {job.name}")

        # Notify the job creator that the report is ready
        try:
            from src.notifications.service import notify_and_broadcast
            await notify_and_broadcast(
                db,
                job.created_by,
                type="report",
                title=f"Report Ready: {job.name}",
                message=(
                    f"Your scheduled {job.report_type} report has completed."
                ),
                data={"job_id": job.id, "report_type": job.report_type},
            )
        except Exception as notify_err:
            logger.warning(f"Failed to send report notification: {notify_err}")

        return True

    except Exception as e:
        logger.error(f"Failed to execute job {job.name}: {e}")
        return False
