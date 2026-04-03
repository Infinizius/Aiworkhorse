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
    user_id = Column(String(255), nullable=False, index=True, default="system_default")
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
    # 768 dimensions: Google text-embedding-004
    embedding = Column(Vector(768), nullable=True)

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
