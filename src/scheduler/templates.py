SCHEDULE_TEMPLATES = {
    "daily_standup": {
        "name": "Daily Standup Report",
        "description": "Daily summary of commits, PRs, and issues for the team standup",
        "report_type": "activity",
        "schedule": "daily",
        "config": {
            "period_days": 1,
            "include_prs": True,
            "include_issues": True,
            "include_commits": True,
        },
    },
    "weekly_digest": {
        "name": "Weekly Team Digest",
        "description": "Weekly summary of team activity and key metrics",
        "report_type": "activity",
        "schedule": "weekly",
        "config": {
            "period_days": 7,
            "include_prs": True,
            "include_issues": True,
            "include_commits": True,
            "include_releases": True,
        },
    },
    "monthly_quality": {
        "name": "Monthly Quality Report",
        "description": "Monthly code quality metrics and trends",
        "report_type": "quality",
        "schedule": "monthly",
        "config": {
            "period_days": 30,
            "include_security": True,
            "include_coverage": True,
        },
    },
    "release_tracker": {
        "name": "Release Tracker",
        "description": "Track releases as they happen",
        "report_type": "releases",
        "schedule": "daily",
        "config": {"period_days": 1},
    },
    "security_weekly": {
        "name": "Weekly Security Scan",
        "description": "Weekly security alerts and vulnerability summary",
        "report_type": "quality",
        "schedule": "weekly",
        "config": {
            "period_days": 7,
            "include_security": True,
            "security_only": True,
        },
    },
}
