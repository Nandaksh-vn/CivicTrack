"""Initial schema: 5 tables implemented through Phase 6 (19.3 baseline).

Revision ID: 0001_initial
Revises: None
Create Date: 2026-11-06

Later phases add the remaining 6 tables (complaint_images,
complaint_status_history, complaint_comments, notifications, escalations,
officer_actions) as incremental migrations. This baseline covers exactly
what the current SQLAlchemy models declare so `alembic upgrade head` from
a clean clone produces a bootable database for Phase 19.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=190), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_role_active", "users", ["role", "is_active"])
    op.create_index("ix_users_dept_role", "users", ["department_id", "role"])
    op.create_table(
        "complaint_categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("default_priority", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(
        "ix_categories_dept_active", "complaint_categories", ["department_id", "is_active"]
    )
    op.create_table(
        "complaints",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("complaint_number", sa.String(length=20), nullable=False),
        sa.Column("citizen_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location_text", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 6), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("accepted_by_user_id", sa.Integer(), nullable=True),
        sa.Column("sla_seconds", sa.Integer(), nullable=True),
        sa.Column("resolution_due_at", sa.DateTime(), nullable=True),
        sa.Column("escalated_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("rejected_at", sa.DateTime(), nullable=True),
        sa.Column("rejected_by_user_id", sa.Integer(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("reopened_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["accepted_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["category_id"], ["complaint_categories.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["citizen_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["rejected_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["resolved_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("complaint_number"),
    )
    op.create_index(
        "ix_complaints_dept_status_sub",
        "complaints",
        ["department_id", "status", "submitted_at"],
    )
    op.create_index("ix_complaints_citizen_sub", "complaints", ["citizen_id", "submitted_at"])
    op.create_index("ix_complaints_status_due", "complaints", ["status", "resolution_due_at"])
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_role", sa.String(length=40), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=60), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_audit_actor", "audit_logs", ["actor_user_id", "created_at"])
    op.create_index("ix_audit_action", "audit_logs", ["action", "created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("complaints")
    op.drop_table("complaint_categories")
    op.drop_table("users")
    op.drop_table("departments")
