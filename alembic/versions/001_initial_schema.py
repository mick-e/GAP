"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("role", sa.String(50), server_default="user"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("hashed_key", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("prefix", sa.String(10), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("permissions", sa.JSON(), server_default="{}"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("report_type", sa.String(50), nullable=False, index=True),
        sa.Column("period", sa.String(20), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False, index=True),
        sa.Column("repo_name", sa.String(255), nullable=True, index=True),
        sa.Column("snapshot_type", sa.String(50), nullable=False),
        sa.Column("commit_count", sa.Integer(), server_default="0"),
        sa.Column("pr_count", sa.Integer(), server_default="0"),
        sa.Column("open_issues", sa.Integer(), server_default="0"),
        sa.Column("closed_issues", sa.Integer(), server_default="0"),
        sa.Column("security_alerts", sa.Integer(), server_default="0"),
        sa.Column("contributors_count", sa.Integer(), server_default="0"),
        sa.Column("metrics", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "webhook_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(50), nullable=False, index=True),
        sa.Column("action", sa.String(50), nullable=True),
        sa.Column("repo_name", sa.String(255), nullable=True, index=True),
        sa.Column("sender", sa.String(255), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("delivery_id", sa.String(36), unique=True, nullable=True),
        sa.Column("processed", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "scheduled_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("schedule", sa.String(50), nullable=False),
        sa.Column("recipients", sa.JSON(), server_default="[]"),
        sa.Column("config", sa.JSON(), server_default="{}"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1")),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "contributors",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("login", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("html_url", sa.String(500), nullable=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("total_commits", sa.Integer(), server_default="0"),
        sa.Column("total_prs", sa.Integer(), server_default="0"),
        sa.Column("total_issues", sa.Integer(), server_default="0"),
        sa.Column("total_reviews", sa.Integer(), server_default="0"),
        sa.Column("lines_added", sa.Integer(), server_default="0"),
        sa.Column("lines_removed", sa.Integer(), server_default="0"),
        sa.Column("repos", sa.JSON(), server_default="[]"),
        sa.Column("metrics", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "team_metrics",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("metrics_date", sa.Date(), nullable=False, index=True),
        sa.Column("repo_name", sa.String(255), nullable=True, index=True),
        sa.Column("deployment_frequency", sa.Float(), server_default="0.0"),
        sa.Column("lead_time_hours", sa.Float(), server_default="0.0"),
        sa.Column("mttr_hours", sa.Float(), server_default="0.0"),
        sa.Column("change_failure_rate", sa.Float(), server_default="0.0"),
        sa.Column("total_commits", sa.Integer(), server_default="0"),
        sa.Column("total_prs", sa.Integer(), server_default="0"),
        sa.Column("total_releases", sa.Integer(), server_default="0"),
        sa.Column("contributors_count", sa.Integer(), server_default="0"),
        sa.Column("extra_metrics", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("team_metrics")
    op.drop_table("contributors")
    op.drop_table("scheduled_jobs")
    op.drop_table("webhook_events")
    op.drop_table("snapshots")
    op.drop_table("reports")
    op.drop_table("api_keys")
    op.drop_table("users")
