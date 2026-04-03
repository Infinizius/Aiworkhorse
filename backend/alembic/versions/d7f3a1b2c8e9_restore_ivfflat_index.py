"""Restore IVFFlat cosine index on file_embeddings.embedding

The previous migration (c1c21ee5d1e1) dropped the IVFFlat index on
file_embeddings.embedding but did not recreate it, causing vector similarity
searches to degrade to a full sequential scan.

Revision ID: d7f3a1b2c8e9
Revises: c1c21ee5d1e1
Create Date: 2026-04-03
"""
from typing import Sequence, Union

from alembic import op

revision: str = "d7f3a1b2c8e9"
down_revision: Union[str, None] = "c1c21ee5d1e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Recreate the IVFFlat cosine index that was accidentally dropped in c1c21ee5d1e1.
    # This index is required for approximate nearest-neighbour search in the RAG pipeline.
    op.execute(
        "CREATE INDEX IF NOT EXISTS file_embeddings_embedding_idx "
        "ON file_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS file_embeddings_embedding_idx")
