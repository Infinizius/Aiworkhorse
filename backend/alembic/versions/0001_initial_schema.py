"""Initial schema: uploaded_files and file_embeddings tables with pgvector.

Revision ID: 0001
Revises:
Create Date: 2026-03-31
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "uploaded_files",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("path", sa.String(512), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column(
            "uploaded_at",
            sa.DateTime(),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )

    op.create_table(
        "file_embeddings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "file_id",
            sa.String(36),
            sa.ForeignKey("uploaded_files.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        # 768-dimensional vector for Google text-embedding-004
        sa.Column("embedding", sa.Text(), nullable=True),  # placeholder; pgvector type applied below
    )

    # Replace the placeholder TEXT column with the real VECTOR(768) type
    op.execute(
        "ALTER TABLE file_embeddings ALTER COLUMN embedding TYPE vector(768) USING NULL::vector"
    )

    # Index for approximate nearest-neighbour search (IVFFlat cosine)
    op.execute(
        "CREATE INDEX ON file_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.drop_table("file_embeddings")
    op.drop_table("uploaded_files")
