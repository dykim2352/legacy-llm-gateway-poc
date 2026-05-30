from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLogRecord(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    role: Mapped[str | None] = mapped_column(String(30), nullable=True)
    path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)

