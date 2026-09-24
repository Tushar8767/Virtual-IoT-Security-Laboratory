"""
Audit Log Model and Repository

Every security-relevant action produces an audit record.
Audit records are append-only — never modified after creation.

Fields:
    timestamp    — when the event occurred
    actor        — who/what performed the action (system, device_id, api)
    action       — what was done (DEVICE_CREATED, DEVICE_SUSPENDED, etc.)
    target       — what was acted upon (device_id, etc.)
    result       — SUCCESS or FAILURE
    correlation_id — links related events
    metadata     — additional context (no secrets)
"""

from enum import Enum
from datetime import datetime, timezone
from typing import Optional
import structlog

from app.core.database import get_database
from app.core.security import generate_event_id

logger = structlog.get_logger(__name__)

COLLECTION = "audit_logs"


class AuditAction(str, Enum):
    """Audit log action types."""
    # Device lifecycle
    DEVICE_CREATED = "DEVICE_CREATED"
    DEVICE_UPDATED = "DEVICE_UPDATED"
    DEVICE_PROVISIONED = "DEVICE_PROVISIONED"
    DEVICE_SUSPENDED = "DEVICE_SUSPENDED"
    DEVICE_REINSTATED = "DEVICE_REINSTATED"
    DEVICE_REVOKED = "DEVICE_REVOKED"
    CREDENTIAL_ROTATED = "CREDENTIAL_ROTATED"
    CREDENTIAL_REVOKED = "CREDENTIAL_REVOKED"

    # Authentication
    AUTH_SUCCESS = "AUTH_SUCCESS"
    AUTH_FAILURE = "AUTH_FAILURE"

    # Authorization
    AUTHZ_FAILURE = "AUTHZ_FAILURE"

    # Scenarios
    SCENARIO_STARTED = "SCENARIO_STARTED"
    SCENARIO_STOPPED = "SCENARIO_STOPPED"
    SCENARIO_COMPLETED = "SCENARIO_COMPLETED"

    # Lab
    LAB_STARTED = "LAB_STARTED"
    LAB_STOPPED = "LAB_STOPPED"
    LAB_RESET = "LAB_RESET"

    # Investigation
    INVESTIGATION_OPENED = "INVESTIGATION_OPENED"
    INVESTIGATION_CLOSED = "INVESTIGATION_CLOSED"


class AuditResult(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


def build_audit_record(
    action: AuditAction,
    target: str,
    result: AuditResult = AuditResult.SUCCESS,
    actor: str = "system",
    correlation_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Build an audit log document."""
    return {
        "audit_id": generate_event_id(),
        "timestamp": datetime.now(timezone.utc),
        "actor": actor,
        "action": action.value,
        "target": target,
        "result": result.value,
        "correlation_id": correlation_id,
        "metadata": metadata or {},
    }


class AuditRepository:
    """Append-only audit log repository."""

    def __init__(self, db):
        self.collection = db[COLLECTION]

    async def log(
        self,
        action: AuditAction,
        target: str,
        result: AuditResult = AuditResult.SUCCESS,
        actor: str = "system",
        correlation_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Append an audit record. Returns the saved record."""
        record = build_audit_record(
            action=action,
            target=target,
            result=result,
            actor=actor,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        await self.collection.insert_one(record)
        logger.info(
            "audit_logged",
            action=action.value,
            target=target,
            result=result.value,
            actor=actor,
            correlation_id=correlation_id,
        )
        return record

    async def find_by_target(
        self, target: str, limit: int = 100
    ) -> list[dict]:
        """Get audit records for a specific target (device_id, etc.)."""
        cursor = (
            self.collection.find({"target": target}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def find_recent(self, limit: int = 100) -> list[dict]:
        """Get the most recent audit records."""
        cursor = (
            self.collection.find({}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)


def get_audit_repository() -> AuditRepository:
    """FastAPI dependency — returns an AuditRepository instance."""
    return AuditRepository(get_database())

