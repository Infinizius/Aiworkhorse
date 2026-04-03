"""Add goal_tasks table for phase 2 autonomous goal engine.

Revision ID: e4b7a9c2f6d1
Revises: d7f3a1b2c8e9
Create Date: 2026-04-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e4b7a9c2f6d1"
down_revision: Union[str, None] = "d7f3a1b2c8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "goal_tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("schedule_minutes", sa.Integer(), nullable=True),
        sa.Column("next_run_at", sa.DateTime(), nullable=True),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("last_result", sa.Text(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("run_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_goal_tasks_status"), "goal_tasks", ["status"], unique=False)
    op.create_index(op.f("ix_goal_tasks_user_id"), "goal_tasks", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_goal_tasks_user_id"), table_name="goal_tasks")
    op.drop_index(op.f("ix_goal_tasks_status"), table_name="goal_tasks")
    op.drop_table("goal_tasks")
