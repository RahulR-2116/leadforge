"""Create lead management tables.

Revision ID: 20260717_0001
Revises:
Create Date: 2026-07-17
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260717_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the migration."""
    op.create_table(
        "businesses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("phone_number", sa.String(length=32), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=120), nullable=True),
        sa.Column("country", sa.String(length=120), nullable=True),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("has_website", sa.Boolean(), nullable=False),
        sa.Column("google_maps_url", sa.String(length=750), nullable=True),
        sa.Column("justdial_url", sa.String(length=750), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "NEW",
                "CONTACTED",
                "REPLIED",
                "DEMO_REQUESTED",
                "DEMO_SENT",
                "NEGOTIATING",
                "CLIENT",
                "LOST",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone_number"),
    )
    op.create_index(
        op.f("ix_businesses_business_name"), "businesses", ["business_name"], unique=False
    )
    op.create_index(op.f("ix_businesses_category"), "businesses", ["category"], unique=False)
    op.create_index(op.f("ix_businesses_city"), "businesses", ["city"], unique=False)
    op.create_index(op.f("ix_businesses_has_website"), "businesses", ["has_website"], unique=False)
    op.create_index(op.f("ix_businesses_id"), "businesses", ["id"], unique=False)
    op.create_index(
        op.f("ix_businesses_phone_number"), "businesses", ["phone_number"], unique=False
    )
    op.create_index(op.f("ix_businesses_state"), "businesses", ["state"], unique=False)
    op.create_index(op.f("ix_businesses_status"), "businesses", ["status"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "statistics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("period", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_statistics_id"), "statistics", ["id"], unique=False)
    op.create_index(op.f("ix_statistics_metric_name"), "statistics", ["metric_name"], unique=False)

    op.create_table(
        "demos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("demo_url", sa.String(length=750), nullable=True),
        sa.Column("video_url", sa.String(length=750), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_demos_id"), "demos", ["id"], unique=False)

    op.create_table(
        "follow_ups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_follow_ups_id"), "follow_ups", ["id"], unique=False)

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("sent", sa.Boolean(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_messages_id"), "messages", ["id"], unique=False)


def downgrade() -> None:
    """Revert the migration."""
    op.drop_index(op.f("ix_messages_id"), table_name="messages")
    op.drop_table("messages")
    op.drop_index(op.f("ix_follow_ups_id"), table_name="follow_ups")
    op.drop_table("follow_ups")
    op.drop_index(op.f("ix_demos_id"), table_name="demos")
    op.drop_table("demos")
    op.drop_index(op.f("ix_statistics_metric_name"), table_name="statistics")
    op.drop_index(op.f("ix_statistics_id"), table_name="statistics")
    op.drop_table("statistics")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_businesses_status"), table_name="businesses")
    op.drop_index(op.f("ix_businesses_state"), table_name="businesses")
    op.drop_index(op.f("ix_businesses_phone_number"), table_name="businesses")
    op.drop_index(op.f("ix_businesses_id"), table_name="businesses")
    op.drop_index(op.f("ix_businesses_has_website"), table_name="businesses")
    op.drop_index(op.f("ix_businesses_city"), table_name="businesses")
    op.drop_index(op.f("ix_businesses_category"), table_name="businesses")
    op.drop_index(op.f("ix_businesses_business_name"), table_name="businesses")
    op.drop_table("businesses")
