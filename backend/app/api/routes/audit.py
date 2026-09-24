"""
Audit Log API Router — Query & Cryptographic Verification

Endpoints:
    GET /api/audit/               — recent audit records
    GET /api/audit/verify         — run cryptographic tamper verification
    GET /api/audit/summary        — count of audit actions
    GET /api/audit/{target}       — audit records for a target
"""

from fastapi import APIRouter, Query, Depends
from app.models.audit import AuditRepository, get_audit_repository
from app.services.audit_verifier import AuditLogVerifier

router = APIRouter(prefix="/audit", tags=["Audit"])


def get_verifier(repo: AuditRepository = Depends(get_audit_repository)) -> AuditLogVerifier:
    return AuditLogVerifier(repo)


@router.get("/", summary="List recent audit records")
async def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    records = await audit_repo.find_recent(limit=limit)
    return {"audit_logs": records, "count": len(records)}


@router.get("/verify", summary="Verify cryptographic audit log integrity")
async def verify_audit_log_integrity(
    verifier: AuditLogVerifier = Depends(get_verifier),
):
    """
    Scans the entire audit log chain sequentially, verifying SHA-256 hashes
    and link integrity to prove no records have been altered or deleted.
    """
    res = await verifier.verify_chain()
    return {
        "status": "VALID" if res.is_valid else "TAMPERED",
        "is_valid": res.is_valid,
        "verified_records": res.verified_count,
        "corrupted_record": res.corrupted_record,
        "reason": res.reason,
    }


@router.get("/{target}", summary="Audit records for a target")
async def get_audit_for_target(
    target: str,
    limit: int = Query(default=100, ge=1, le=500),
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    records = await audit_repo.find_by_target(target, limit=limit)
    return {"target": target, "audit_logs": records, "count": len(records)}