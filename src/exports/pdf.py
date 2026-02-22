from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from src.reports.schemas import ActivityReport, QualityReport, ReleaseReport


class PDFExporter:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name="ReportTitle",
            parent=self.styles["Heading1"],
            fontSize=24,
            spaceAfter=30,
        ))
        self.styles.add(ParagraphStyle(
            name="SectionTitle",
            parent=self.styles["Heading2"],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
        ))
        self.styles.add(ParagraphStyle(
            name="SubSection",
            parent=self.styles["Heading3"],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=5,
        ))

    def _create_table(self, data: list[list], col_widths: list[float] | None = None) -> Table:
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a73e8")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#dee2e6")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ]))
        return table

    def export_activity_report(self, report: ActivityReport) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []

        # Title
        elements.append(Paragraph(f"Activity Report: {report.org_name}", self.styles["ReportTitle"]))
        elements.append(Paragraph(
            f"Period: {report.period.value} ({report.start_date.strftime('%Y-%m-%d')} to {report.end_date.strftime('%Y-%m-%d')})",
            self.styles["Normal"]
        ))
        elements.append(Paragraph(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}", self.styles["Normal"]))
        elements.append(Spacer(1, 20))

        # Summary table
        elements.append(Paragraph("Organization Summary", self.styles["SectionTitle"]))
        summary_data = [
            ["Metric", "Value"],
            ["Total Commits", str(report.totals.get("total_commits", 0))],
            ["Total Pull Requests", str(report.totals.get("total_prs", 0))],
            ["Total Issues", str(report.totals.get("total_issues", 0))],
            ["Repositories Analyzed", str(len(report.repos))],
        ]
        elements.append(self._create_table(summary_data, [3*inch, 2*inch]))
        elements.append(Spacer(1, 20))

        # Per-repo details
        for repo in report.repos:
            elements.append(Paragraph(f"Repository: {repo.repo_name}", self.styles["SectionTitle"]))

            # Commits
            elements.append(Paragraph("Commits", self.styles["SubSection"]))
            commits_data = [
                ["Total", "Additions", "Deletions", "Files Changed"],
                [
                    str(repo.commits.total_commits),
                    str(repo.commits.total_additions),
                    str(repo.commits.total_deletions),
                    str(repo.commits.total_files_changed),
                ],
            ]
            elements.append(self._create_table(commits_data))

            # PRs
            elements.append(Paragraph("Pull Requests", self.styles["SubSection"]))
            pr_data = [
                ["Total", "Open", "Merged", "Closed", "Avg Merge Time (hrs)"],
                [
                    str(repo.pull_requests.total_prs),
                    str(repo.pull_requests.open_prs),
                    str(repo.pull_requests.merged_prs),
                    str(repo.pull_requests.closed_prs),
                    f"{repo.pull_requests.avg_merge_time_hours:.1f}" if repo.pull_requests.avg_merge_time_hours else "N/A",
                ],
            ]
            elements.append(self._create_table(pr_data))

            # Issues
            elements.append(Paragraph("Issues", self.styles["SubSection"]))
            issue_data = [
                ["Total", "Open", "Closed", "Avg Close Time (hrs)"],
                [
                    str(repo.issues.total_issues),
                    str(repo.issues.open_issues),
                    str(repo.issues.closed_issues),
                    f"{repo.issues.avg_close_time_hours:.1f}" if repo.issues.avg_close_time_hours else "N/A",
                ],
            ]
            elements.append(self._create_table(issue_data))

            # Top contributors
            if repo.top_contributors:
                elements.append(Paragraph("Top Contributors", self.styles["SubSection"]))
                contrib_data = [["Username", "Commits", "PRs"]]
                for c in repo.top_contributors[:5]:
                    contrib_data.append([c.login, str(c.commits), str(c.prs)])
                elements.append(self._create_table(contrib_data))

            elements.append(Spacer(1, 20))

        doc.build(elements)
        return buffer.getvalue()

    def export_quality_report(self, report: QualityReport) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []

        # Title
        elements.append(Paragraph(f"Code Quality Report: {report.org_name}", self.styles["ReportTitle"]))
        elements.append(Paragraph(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}", self.styles["Normal"]))
        elements.append(Spacer(1, 20))

        # Security summary
        elements.append(Paragraph("Security Summary (All Repositories)", self.styles["SectionTitle"]))
        security_data = [
            ["Alert Type", "Count"],
            ["Code Scanning", str(report.totals.code_scanning_alerts)],
            ["Dependabot", str(report.totals.dependabot_alerts)],
            ["Secret Scanning", str(report.totals.secret_scanning_alerts)],
        ]
        elements.append(self._create_table(security_data, [3*inch, 2*inch]))
        elements.append(Spacer(1, 10))

        severity_data = [
            ["Severity", "Count"],
            ["Critical", str(report.totals.critical_alerts)],
            ["High", str(report.totals.high_alerts)],
            ["Medium", str(report.totals.medium_alerts)],
            ["Low", str(report.totals.low_alerts)],
        ]
        elements.append(self._create_table(severity_data, [3*inch, 2*inch]))
        elements.append(Spacer(1, 20))

        # Per-repo details
        for repo in report.repos:
            elements.append(Paragraph(f"Repository: {repo.repo_name}", self.styles["SectionTitle"]))

            # Workflows
            if repo.workflows:
                elements.append(Paragraph("CI/CD Workflows", self.styles["SubSection"]))
                wf_data = [["Workflow", "Total Runs", "Success", "Failed", "Success Rate"]]
                for wf in repo.workflows:
                    wf_data.append([
                        wf.workflow_name[:30],
                        str(wf.total_runs),
                        str(wf.successful_runs),
                        str(wf.failed_runs),
                        f"{wf.success_rate:.1f}%",
                    ])
                elements.append(self._create_table(wf_data))

            # Languages
            if repo.languages:
                elements.append(Paragraph("Languages", self.styles["SubSection"]))
                total_bytes = sum(repo.languages.values())
                lang_data = [["Language", "Bytes", "Percentage"]]
                for lang, bytes_count in sorted(repo.languages.items(), key=lambda x: -x[1])[:5]:
                    pct = bytes_count / total_bytes * 100 if total_bytes > 0 else 0
                    lang_data.append([lang, f"{bytes_count:,}", f"{pct:.1f}%"])
                elements.append(self._create_table(lang_data))

            elements.append(Spacer(1, 20))

        doc.build(elements)
        return buffer.getvalue()

    def export_release_report(self, report: ReleaseReport) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []

        # Title
        elements.append(Paragraph(f"Release Report: {report.org_name}", self.styles["ReportTitle"]))
        elements.append(Paragraph(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}", self.styles["Normal"]))
        elements.append(Paragraph(f"Total Releases: {report.total_releases}", self.styles["Normal"]))
        elements.append(Spacer(1, 20))

        # Per-repo details
        for repo in report.repos:
            elements.append(Paragraph(f"Repository: {repo.repo_name}", self.styles["SectionTitle"]))
            elements.append(Paragraph(f"Total Releases: {repo.total_releases} | Tags: {repo.tags_count}", self.styles["Normal"]))

            if repo.latest_release:
                elements.append(Paragraph("Latest Release", self.styles["SubSection"]))
                latest_data = [
                    ["Field", "Value"],
                    ["Tag", repo.latest_release.tag_name],
                    ["Name", repo.latest_release.name or "N/A"],
                    ["Author", repo.latest_release.author],
                    ["Published", repo.latest_release.published_at.strftime("%Y-%m-%d") if repo.latest_release.published_at else "N/A"],
                    ["Pre-release", "Yes" if repo.latest_release.prerelease else "No"],
                ]
                elements.append(self._create_table(latest_data, [2*inch, 4*inch]))

            if repo.releases:
                elements.append(Paragraph("All Releases", self.styles["SubSection"]))
                release_data = [["Tag", "Name", "Author", "Published", "Pre-release"]]
                for r in repo.releases[:10]:  # Limit to 10
                    release_data.append([
                        r.tag_name,
                        (r.name or "N/A")[:30],
                        r.author,
                        r.published_at.strftime("%Y-%m-%d") if r.published_at else "N/A",
                        "Yes" if r.prerelease else "No",
                    ])
                elements.append(self._create_table(release_data))

            elements.append(Spacer(1, 20))

        doc.build(elements)
        return buffer.getvalue()
