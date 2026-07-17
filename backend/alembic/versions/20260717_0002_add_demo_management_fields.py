"""Add demo management fields.

Revision ID: 20260717_0002
Revises: 20260717_0001
Create Date: 2026-07-17
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260717_0002"
down_revision = "20260717_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the migration."""
    op.add_column(
        "demos",
        sa.Column(
            "deployment_status",
            sa.String(length=50),
            nullable=False,
            server_default="draft",
        ),
    )
    op.add_column("demos", sa.Column("deployment_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("demos", sa.Column("revision_history", sa.Text(), nullable=True))
    op.add_column("demos", sa.Column("template_used", sa.String(length=120), nullable=True))
    op.add_column("demos", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column(
        "demos", sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.false())
    )


def downgrade() -> None:
    """Revert the migration."""
    op.drop_column("demos", "archived")
    op.drop_column("demos", "version")
    op.drop_column("demos", "template_used")
    op.drop_column("demos", "revision_history")
    op.drop_column("demos", "deployment_date")
    op.drop_column("demos", "deployment_status")
