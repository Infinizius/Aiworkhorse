"""Add user_vault table for Phase 1 Token Vault.

Revision ID: f1a2b3c4d5e6
Revises: b5c4d3e2f1a0, 9e3b1f2a4c6d
Create Date: 2026-04-07
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str]] = ("b5c4d3e2f1a0", "9e3b1f2a4c6d")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_vault",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("openwebui_api_key", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_vault_user_id"), "user_vault", ["user_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_vault_user_id"), table_name="user_vault")
    op.drop_table("user_vault")
