"""Add GitHub OAuth columns to users table

Revision ID: 003
Revises: 002
Create Date: 2026-03-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("github_id", sa.String(50), unique=True, nullable=True, index=True),
    )
    op.add_column(
        "users",
        sa.Column("avatar_url", sa.String(500), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("auth_provider", sa.String(20), server_default="local"),
    )


def downgrade() -> None:
    op.drop_column("users", "auth_provider")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "github_id")
