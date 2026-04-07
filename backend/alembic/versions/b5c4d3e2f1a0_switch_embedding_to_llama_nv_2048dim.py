"""Switch embedding column from vector(1024) to vector(2048) for NVIDIA llama-3.2-nv-embedqa-1b-v2.

nvidia/nv-embedqa-e5-v5 produced 1024-dimensional vectors.  The new
nvidia/llama-3.2-nv-embedqa-1b-v2 model produces 2048-dimensional vectors and
is more powerful for retrieval / RAG workloads.

Existing embeddings are incompatible with the new model and are cleared so
that they are regenerated the next time a user re-uploads their documents.

Revision ID: b5c4d3e2f1a0
Revises: a3f2e1d0c9b8
Create Date: 2026-04-07
"""
from typing import Sequence, Union

from alembic import op

revision: str = "b5c4d3e2f1a0"
down_revision: Union[str, None] = "a3f2e1d0c9b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Remove all existing 1024-dim embeddings – they are incompatible with
    #    the new 2048-dim NVIDIA model and must be regenerated.
    op.execute("DELETE FROM file_embeddings")

    # 2. Drop the IVFFlat index before altering the column type.
    op.execute("DROP INDEX IF EXISTS file_embeddings_embedding_idx")

    # 3. Change the embedding column from vector(1024) to vector(2048).
    op.execute(
        "ALTER TABLE file_embeddings ALTER COLUMN embedding TYPE vector(2048)"
    )

    # 4. Recreate the IVFFlat cosine index for approximate nearest-neighbour search.
    op.execute(
        "CREATE INDEX file_embeddings_embedding_idx "
        "ON file_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    # 1. Clear embeddings – 2048-dim vectors are incompatible with vector(1024).
    op.execute("DELETE FROM file_embeddings")

    # 2. Drop current index.
    op.execute("DROP INDEX IF EXISTS file_embeddings_embedding_idx")

    # 3. Revert column to vector(1024).
    op.execute(
        "ALTER TABLE file_embeddings ALTER COLUMN embedding TYPE vector(1024)"
    )

    # 4. Recreate the index for the previous dimensions.
    op.execute(
        "CREATE INDEX file_embeddings_embedding_idx "
        "ON file_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
