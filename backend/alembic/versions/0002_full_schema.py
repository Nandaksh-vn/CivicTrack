"""Full schema: remaining 6 tables, integrity checks, missing indexes (DB-007..DB-016).

Revision ID: 0002_full_schema
Revises: 0001_initial
Create Date: 2026-11-06
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_full_schema"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "complaint_images",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("complaint_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("size_bytes >= 0", name="ck_complaint_images_size_nonnegative"),
    )
    op.create_index(
        "ix_complaint_images_complaint_created",
        "complaint_images",
        ["complaint_id", "created_at"],
    )

    op.create_table(
        "complaint_status_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("complaint_id", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.String(length=40), nullable=True),
        sa.Column("to_status", sa.String(length=40), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_role", sa.String(length=40), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_status_history_complaint_created",
        "complaint_status_history",
        ["complaint_id", "created_at"],
    )

    op.create_table(
        "complaint_comments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("complaint_id", sa.Integer(), nullable=False),
        sa.Column("author_user_id", sa.Integer(), nullable=False),
        sa.Column("comment_type", sa.String(length=40), nullable=False),
        sa.Column("visibility", sa.String(length=40), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("LENGTH(body) > 0", name="ck_comments_body_nonempty"),
    )
    op.create_index(
        "ix_comments_complaint_created",
        "complaint_comments",
        ["complaint_id", "created_at"],
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("recipient_user_id", sa.Integer(), nullable=False),
        sa.Column("complaint_id", sa.Integer(), nullable=True),
        sa.Column("trigger_code", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notifications_recipient_read",
        "notifications",
        ["recipient_user_id", "is_read"],
    )
    op.create_index("ix_notifications_complaint", "notifications", ["complaint_id"])
    op.create_index("ix_notifications_trigger", "notifications", ["trigger_code", "created_at"])

    op.create_table(
        "escalations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("complaint_id", sa.Integer(), nullable=False),
        sa.Column("escalation_number", sa.String(length=32), nullable=True),
        sa.Column("previous_status", sa.String(length=40), nullable=False),
        sa.Column("deadline_at", sa.DateTime(), nullable=False),
        sa.Column("escalated_at", sa.DateTime(), nullable=False),
        sa.Column("overdue_seconds", sa.Integer(), nullable=False),
        sa.Column("trigger_source", sa.String(length=40), nullable=False),
        sa.Column("reason_code", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("complaint_id", name="uq_escalations_complaint"),
        sa.UniqueConstraint("escalation_number", name="uq_escalations_number"),
        sa.CheckConstraint("overdue_seconds >= 0", name="ck_escalations_overdue_nonnegative"),
    )
    op.create_index("ix_escalations_deadline", "escalations", ["deadline_at"])

    op.create_table(
        "officer_actions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("complaint_id", sa.Integer(), nullable=False),
        sa.Column("officer_user_id", sa.Integer(), nullable=False),
        sa.Column("directed_department_id", sa.Integer(), nullable=True),
        sa.Column("action_type", sa.String(length=40), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["officer_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["directed_department_id"], ["departments.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("LENGTH(note) > 0", name="ck_officer_actions_note_nonempty"),
    )
    op.create_index(
        "ix_officer_actions_complaint_created",
        "officer_actions",
        ["complaint_id", "created_at"],
    )
    op.create_index(
        "ix_officer_actions_officer",
        "officer_actions",
        ["officer_user_id", "created_at"],
    )

    # Integrity checks on complaints (TRD §7.x)
    op.create_check_constraint(
        "ck_complaints_coordinates_paired",
        "complaints",
        "(latitude IS NULL) = (longitude IS NULL)",
    )
    op.create_check_constraint(
        "ck_complaints_latitude_range",
        "complaints",
        "latitude BETWEEN -90 AND 90 OR latitude IS NULL",
    )
    op.create_check_constraint(
        "ck_complaints_longitude_range",
        "complaints",
        "longitude BETWEEN -180 AND 180 OR longitude IS NULL",
    )
    op.create_check_constraint(
        "ck_complaints_deadline_requires_acceptance",
        "complaints",
        "resolution_due_at IS NULL OR accepted_at IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_constraint("ck_complaints_deadline_requires_acceptance", "complaints", type_="check")
    op.drop_constraint("ck_complaints_longitude_range", "complaints", type_="check")
    op.drop_constraint("ck_complaints_latitude_range", "complaints", type_="check")
    op.drop_constraint("ck_complaints_coordinates_paired", "complaints", type_="check")

    op.drop_table("officer_actions")

    op.drop_table("escalations")

    op.drop_table("notifications")

    op.drop_table("complaint_comments")

    op.drop_table("complaint_status_history")

    op.drop_table("complaint_images")
