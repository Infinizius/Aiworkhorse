"""Add user ownership to uploaded files

Revision ID: 9e3b1f2a4c6d
Revises: c1c21ee5d1e1
Create Date: 2026-04-03 17:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9e3b1f2a4c6d"
down_revision: Union[str, None] = "c1c21ee5d1e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "uploaded_files",
        sa.Column(
            "user_id",
            sa.String(length=255),
            nullable=False,
            server_default="system_default",
        ),
    )
    op.create_index(op.f("ix_uploaded_files_user_id"), "uploaded_files", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_uploaded_files_user_id"), table_name="uploaded_files")
    op.drop_column("uploaded_files", "user_id")
