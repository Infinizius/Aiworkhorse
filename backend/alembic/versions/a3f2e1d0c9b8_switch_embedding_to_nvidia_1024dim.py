"""Switch embedding column from vector(768) to vector(1024) for NVIDIA nv-embedqa-e5-v5.

Google text-embedding-004 produced 768-dimensional vectors.  The new
nvidia/nv-embedqa-e5-v5 model produces 1024-dimensional vectors and is
optimised for retrieval / RAG workloads.

Existing embeddings are incompatible with the new model and are cleared so
that they are regenerated the next time a user re-uploads their documents.

Revision ID: a3f2e1d0c9b8
Revises: e4b7a9c2f6d1
Create Date: 2026-04-07
"""
from typing import Sequence, Union

from alembic import op

revision: str = "a3f2e1d0c9b8"
down_revision: Union[str, None] = "e4b7a9c2f6d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Remove all existing 768-dim embeddings – they are incompatible with
    #    the new 1024-dim NVIDIA model and must be regenerated.
    op.execute("DELETE FROM file_embeddings")

    # 2. Drop the IVFFlat index before altering the column type.
    op.execute("DROP INDEX IF EXISTS file_embeddings_embedding_idx")

    # 3. Change the embedding column from vector(768) to vector(1024).
    op.execute(
        "ALTER TABLE file_embeddings ALTER COLUMN embedding TYPE vector(1024)"
    )

    # 4. Recreate the IVFFlat cosine index for approximate nearest-neighbour search.
    op.execute(
        "CREATE INDEX file_embeddings_embedding_idx "
        "ON file_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    # 1. Clear embeddings – 1024-dim vectors are incompatible with vector(768).
    op.execute("DELETE FROM file_embeddings")

    # 2. Drop current index.
    op.execute("DROP INDEX IF EXISTS file_embeddings_embedding_idx")

    # 3. Revert column to vector(768).
    op.execute(
        "ALTER TABLE file_embeddings ALTER COLUMN embedding TYPE vector(768)"
    )

    # 4. Recreate the index for the original dimensions.
    op.execute(
        "CREATE INDEX file_embeddings_embedding_idx "
        "ON file_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
