"""
Audit Log Cryptographic Verifier

Walks the audit log chain from genesis to head, recalculating hashes.
Detects tampering, record deletions, or payload modifications.
"""

from typing import Dict, Any, List
import structlog
from app.models.audit import AuditRepository, compute_audit_hash

logger = structlog.get_logger(__name__)


class AuditVerificationResult:
    def __init__(self, is_valid: bool, verified_count: int, corrupted_record: Any = None, reason: str = ""):
        self.is_valid = is_valid
        self.verified_count = verified_count
        self.corrupted_record = corrupted_record
        self.reason = reason


class AuditLogVerifier:
    """Verifies cryptographic integrity of the audit trail."""

    def __init__(self, audit_repo: AuditRepository):
        self.audit_repo = audit_repo

    async def verify_chain(self) -> AuditVerificationResult:
        records: List[Dict[str, Any]] = await self.audit_repo.get_all_ordered_for_verification()

        if not records:
            return AuditVerificationResult(True, 0, reason="Audit log is empty (VALID)")

        expected_prev_hash = "GENESIS_BLOCK_HASH"

        for idx, rec in enumerate(records):
            # 1. Check prev_hash link
            actual_prev = rec.get("prev_hash")
            if actual_prev != expected_prev_hash:
                logger.error(
                    "audit_chain_broken",
                    index=idx,
                    expected=expected_prev_hash,
                    actual=actual_prev,
                    audit_id=rec.get("audit_id"),
                )
                return AuditVerificationResult(
                    is_valid=False,
                    verified_count=idx,
                    corrupted_record=rec.get("audit_id"),
                    reason=f"Chain broken at record #{idx}: prev_hash mismatch",
                )

            # 2. Recompute entry_hash
            recomputed = compute_audit_hash(rec, actual_prev)
            if recomputed != rec.get("entry_hash"):
                logger.error(
                    "audit_payload_tampered",
                    index=idx,
                    expected=recomputed,
                    actual=rec.get("entry_hash"),
                    audit_id=rec.get("audit_id"),
                )
                return AuditVerificationResult(
                    is_valid=False,
                    verified_count=idx,
                    corrupted_record=rec.get("audit_id"),
                    reason=f"Content modified at record #{idx}: entry_hash mismatch",
                )

            expected_prev_hash = rec.get("entry_hash")

        return AuditVerificationResult(
            is_valid=True,
            verified_count=len(records),
            reason=f"Successfully verified all {len(records)} audit log entries without tampering.",
        )