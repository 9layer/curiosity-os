"""init

Revision ID: 0001
Revises:
Create Date: 2026-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

capture_status = postgresql.ENUM(
    "inbox", "explore", "scheduled", "someday", "archived", "deleted",
    name="capture_status",
)


def upgrade():
    capture_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "projects",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "captures",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("status", capture_status, nullable=False, server_default="inbox"),
        sa.Column("project_id", sa.BigInteger(), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("topic", sa.String(length=200), nullable=True),
        sa.Column("entities", postgresql.JSONB(), nullable=True),
        sa.Column("suggested_project", sa.String(length=120), nullable=True),
        sa.Column("is_question", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=40), server_default="telegram"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_captures_status", "captures", ["status"])
    op.create_index("ix_captures_created_at", "captures", ["created_at"])
    op.create_table(
        "focus_sessions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("project", sa.String(length=120), nullable=True),
        sa.Column("source", sa.String(length=200), nullable=True),
        sa.Column("goal", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_table("focus_sessions")
    op.drop_index("ix_captures_created_at", table_name="captures")
    op.drop_index("ix_captures_status", table_name="captures")
    op.drop_table("captures")
    op.drop_table("projects")
    capture_status.drop(op.get_bind(), checkfirst=True)