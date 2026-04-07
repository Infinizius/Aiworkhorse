import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    path = Column(String(512), nullable=False)
    extracted_text = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    embeddings = relationship(
        "FileEmbedding", back_populates="file", cascade="all, delete-orphan"
    )

class FileEmbedding(Base):
    __tablename__ = "file_embeddings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_id = Column(String(36), ForeignKey("uploaded_files.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    # 1024 dimensions: NVIDIA nv-embedqa-e5-v5
    embedding = Column(Vector(1024), nullable=True)

    file = relationship("UploadedFile", back_populates="embeddings")

class UserConfig(Base):
    __tablename__ = "user_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # User ID or Email from Open WebUI (header X-User-Email)
    user_id = Column(String(255), nullable=False, index=True)
    # "gemini", "mistral", or "deepseek"
    provider = Column(String(50), nullable=False)
    # The encrypted API key
    encrypted_key = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class GoalTask(Base):
    __tablename__ = "goal_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, index=True)
    goal = Column(Text, nullable=False)
    model = Column(String(100), nullable=False, default="gemini-3-flash-preview")
    status = Column(String(32), nullable=False, default="pending", index=True)
    schedule_minutes = Column(Integer, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    last_result = Column(Text, nullable=True)
    last_error = Column(Text, nullable=True)
    run_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
