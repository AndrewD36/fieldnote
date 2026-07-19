from datetime import datetime
from sqlalchemy import DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from research_rag.pipeline.database.db import Base


class PaperRecord(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    arxiv_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    version: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    authors: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
    )

    abstract: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    categories: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
    )

    primary_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    pdf_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    pdf_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    checksum: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    size_bytes: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    download_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    preprocessing_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    database_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )