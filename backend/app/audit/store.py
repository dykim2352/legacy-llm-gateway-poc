from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select

from app.audit.db_models import AuditLogRecord
from app.audit.models import AuditEventType, AuditLogEntry
from app.auth.models import User
from app.core.database import SessionLocal
from app.core.metrics import AUDIT_EVENTS_TOTAL


def append_audit_log(
    event_type: AuditEventType,
    *,
    success: bool,
    message: str,
    user: User | None = None,
    username: str | None = None,
    path: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLogEntry:
    with SessionLocal() as session:
        record = AuditLogRecord(
            timestamp=datetime.now(UTC),
            event_type=event_type.value,
            username=user.username if user is not None else username,
            role=user.role.value if user is not None else None,
            path=path,
            success=success,
            message=message,
            metadata_json=metadata or {},
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        AUDIT_EVENTS_TOTAL.labels(event_type=event_type.value, success=str(success).lower()).inc()
        return _to_entry(record)


def list_audit_logs() -> list[AuditLogEntry]:
    with SessionLocal() as session:
        records = session.scalars(
            select(AuditLogRecord).order_by(AuditLogRecord.timestamp.desc(), AuditLogRecord.id.desc())
        ).all()
        return [_to_entry(record) for record in records]


def clear_audit_logs_for_tests() -> None:
    with SessionLocal() as session:
        session.execute(delete(AuditLogRecord))
        session.commit()


def _to_entry(record: AuditLogRecord) -> AuditLogEntry:
    return AuditLogEntry(
        id=record.id,
        timestamp=record.timestamp,
        event_type=AuditEventType(record.event_type),
        username=record.username,
        role=record.role,
        path=record.path,
        success=record.success,
        message=record.message,
        metadata=record.metadata_json or {},
    )
