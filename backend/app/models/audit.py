"""
Audit Log Model and Repository — Tamper-Evident Cryptographic Hash Chaining

Every security-relevant action produces an append-only audit record.
Each record is cryptographically linked to the previous entry via SHA-256 hash chaining.
"""

from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import hashlib
import json
import structlog

from app.core.database import get_database
from app.core.security import generate_event_id

logger = structlog.get_logger(__name__)

COLLECTION = "audit_logs"


class AuditAction(str, Enum):
    # Device lifecycle
    DEVICE_CREATED = "DEVICE_CREATED"
    DEVICE_UPDATED = "DEVICE_UPDATED"
    DEVICE_PROVISIONED = "DEVICE_PROVISIONED"
    DEVICE_SUSPENDED = "DEVICE_SUSPENDED"
    DEVICE_REINSTATED = "DEVICE_REINSTATED"
    DEVICE_REVOKED = "DEVICE_REVOKED"
    CREDENTIAL_ROTATED = "CREDENTIAL_ROTATED"
    CREDENTIAL_REVOKED = "CREDENTIAL_REVOKED"

    # Authentication & Authorization
    AUTH_SUCCESS = "AUTH_SUCCESS"
    AUTH_FAILURE = "AUTH_FAILURE"
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


def compute_audit_hash(record_data: Dict[str, Any], prev_hash: str) -> str:
    """
    Computes a deterministic SHA-256 hash over the canonical audit record fields.
    """
    canonical_str = (
        f"{record_data.get('audit_id')}|"
        f"{record_data.get('timestamp')}|"
        f"{record_data.get('actor')}|"
        f"{record_data.get('action')}|"
        f"{record_data.get('target')}|"
        f"{record_data.get('result')}|"
        f"{prev_hash}"
    )
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


class AuditRepository:
    """Append-only audit log repository with cryptographic hash-chaining."""

    def __init__(self, db=None):
        self.db = db if db is not None else get_database()
        self.collection = self.db[COLLECTION]

    async def log(
        self,
        action: AuditAction,
        target: str,
        result: AuditResult = AuditResult.SUCCESS,
        actor: str = "system",
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Append a tamper-evident audit record linked to the previous entry.
        """
        audit_id = generate_event_id()
        now_dt = datetime.now(timezone.utc)
        now_str = now_dt.isoformat()

        # Find latest record to retrieve prev_hash
        latest = await self.collection.find({}, {"_id": 0, "entry_hash": 1}).sort("timestamp", -1).limit(1).to_list(length=1)
        prev_hash = latest[0].get("entry_hash", "GENESIS_BLOCK_HASH") if latest else "GENESIS_BLOCK_HASH"

        core_data = {
            "audit_id": audit_id,
            "timestamp": now_str,
            "actor": actor,
            "action": action.value if hasattr(action, "value") else str(action),
            "target": target,
            "result": result.value if hasattr(result, "value") else str(result),
        }

        entry_hash = compute_audit_hash(core_data, prev_hash)

        record = {
            **core_data,
            "timestamp_dt": now_dt,
            "correlation_id": correlation_id,
            "prev_hash": prev_hash,
            "entry_hash": entry_hash,
            "metadata": metadata or {},
        }

        await self.collection.insert_one(record)
        logger.info(
            "audit_logged",
            action=record["action"],
            target=target,
            result=record["result"],
            entry_hash=entry_hash[:12],
        )
        return record

    async def find_by_target(self, target: str, limit: int = 100) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"target": target}, {"_id": 0}).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def find_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        cursor = self.collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_all_ordered_for_verification(self) -> List[Dict[str, Any]]:
        cursor = self.collection.find({}, {"_id": 0}).sort("timestamp", 1)
        return await cursor.to_list(length=None)


def get_audit_repository() -> AuditRepository:
    return AuditRepository(get_database())