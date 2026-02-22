import csv
from io import StringIO

from src.reports.schemas import ActivityReport, QualityReport, ReleaseReport


class CSVExporter:
    def export_activity_report(self, report: ActivityReport) -> str:
        output = StringIO()

        # Summary section
        output.write("# Activity Report Summary\n")
        output.write(f"Organization,{report.org_name}\n")
        output.write(f"Period,{report.period.value}\n")
        output.write(f"Start Date,{report.start_date.isoformat()}\n")
        output.write(f"End Date,{report.end_date.isoformat()}\n")
        output.write(f"Generated,{report.generated_at.isoformat()}\n")
        output.write(f"Total Commits,{report.totals.get('total_commits', 0)}\n")
        output.write(f"Total PRs,{report.totals.get('total_prs', 0)}\n")
        output.write(f"Total Issues,{report.totals.get('total_issues', 0)}\n")
        output.write("\n")

        # Commits by repo
        output.write("# Commits by Repository\n")
        writer = csv.writer(output)
        writer.writerow(["Repository", "Total Commits", "Additions", "Deletions", "Files Changed"])
        for repo in report.repos:
            writer.writerow([
                repo.repo_name,
                repo.commits.total_commits,
                repo.commits.total_additions,
                repo.commits.total_deletions,
                repo.commits.total_files_changed,
            ])
        output.write("\n")

        # PRs by repo
        output.write("# Pull Requests by Repository\n")
        writer.writerow(["Repository", "Total", "Open", "Merged", "Closed", "Avg Merge Time (hrs)"])
        for repo in report.repos:
            writer.writerow([
                repo.repo_name,
                repo.pull_requests.total_prs,
                repo.pull_requests.open_prs,
                repo.pull_requests.merged_prs,
                repo.pull_requests.closed_prs,
                f"{repo.pull_requests.avg_merge_time_hours:.2f}" if repo.pull_requests.avg_merge_time_hours else "",
            ])
        output.write("\n")

        # Issues by repo
        output.write("# Issues by Repository\n")
        writer.writerow(["Repository", "Total", "Open", "Closed", "Avg Close Time (hrs)"])
        for repo in report.repos:
            writer.writerow([
                repo.repo_name,
                repo.issues.total_issues,
                repo.issues.open_issues,
                repo.issues.closed_issues,
                f"{repo.issues.avg_close_time_hours:.2f}" if repo.issues.avg_close_time_hours else "",
            ])
        output.write("\n")

        # Top contributors (flattened)
        output.write("# Top Contributors\n")
        writer.writerow(["Repository", "Username", "Commits", "PRs"])
        for repo in report.repos:
            for c in repo.top_contributors:
                writer.writerow([repo.repo_name, c.login, c.commits, c.prs])

        return output.getvalue()

    def export_quality_report(self, report: QualityReport) -> str:
        output = StringIO()

        # Summary section
        output.write("# Code Quality Report Summary\n")
        output.write(f"Organization,{report.org_name}\n")
        output.write(f"Generated,{report.generated_at.isoformat()}\n")
        output.write(f"Code Scanning Alerts,{report.totals.code_scanning_alerts}\n")
        output.write(f"Dependabot Alerts,{report.totals.dependabot_alerts}\n")
        output.write(f"Secret Scanning Alerts,{report.totals.secret_scanning_alerts}\n")
        output.write(f"Critical Alerts,{report.totals.critical_alerts}\n")
        output.write(f"High Alerts,{report.totals.high_alerts}\n")
        output.write(f"Medium Alerts,{report.totals.medium_alerts}\n")
        output.write(f"Low Alerts,{report.totals.low_alerts}\n")
        output.write("\n")

        # Security by repo
        output.write("# Security Alerts by Repository\n")
        writer = csv.writer(output)
        writer.writerow(["Repository", "Code Scanning", "Dependabot", "Secret Scanning", "Critical", "High", "Medium", "Low"])
        for repo in report.repos:
            s = repo.security
            writer.writerow([
                repo.repo_name,
                s.code_scanning_alerts,
                s.dependabot_alerts,
                s.secret_scanning_alerts,
                s.critical_alerts,
                s.high_alerts,
                s.medium_alerts,
                s.low_alerts,
            ])
        output.write("\n")

        # Workflows
        output.write("# CI/CD Workflows\n")
        writer.writerow(["Repository", "Workflow", "Total Runs", "Successful", "Failed", "Success Rate"])
        for repo in report.repos:
            for wf in repo.workflows:
                writer.writerow([
                    repo.repo_name,
                    wf.workflow_name,
                    wf.total_runs,
                    wf.successful_runs,
                    wf.failed_runs,
                    f"{wf.success_rate:.1f}%",
                ])
        output.write("\n")

        # Languages
        output.write("# Languages by Repository\n")
        writer.writerow(["Repository", "Language", "Bytes"])
        for repo in report.repos:
            for lang, bytes_count in repo.languages.items():
                writer.writerow([repo.repo_name, lang, bytes_count])

        return output.getvalue()

    def export_release_report(self, report: ReleaseReport) -> str:
        output = StringIO()

        # Summary section
        output.write("# Release Report Summary\n")
        output.write(f"Organization,{report.org_name}\n")
        output.write(f"Generated,{report.generated_at.isoformat()}\n")
        output.write(f"Total Releases,{report.total_releases}\n")
        output.write("\n")

        # Releases by repo
        output.write("# Releases by Repository\n")
        writer = csv.writer(output)
        writer.writerow(["Repository", "Tag", "Name", "Author", "Published", "Pre-release"])
        for repo in report.repos:
            for r in repo.releases:
                writer.writerow([
                    repo.repo_name,
                    r.tag_name,
                    r.name or "",
                    r.author,
                    r.published_at.isoformat() if r.published_at else "",
                    "Yes" if r.prerelease else "No",
                ])
        output.write("\n")

        # Summary per repo
        output.write("# Repository Summary\n")
        writer.writerow(["Repository", "Total Releases", "Tags Count", "Latest Release"])
        for repo in report.repos:
            writer.writerow([
                repo.repo_name,
                repo.total_releases,
                repo.tags_count,
                repo.latest_release.tag_name if repo.latest_release else "",
            ])

        return output.getvalue()
