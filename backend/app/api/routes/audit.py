"""
Audit Log API Router — Phase 1 Implementation (basic read)

Endpoints:
    GET /api/audit/               — recent audit records
    GET /api/audit/{target}       — audit records for a specific target
"""

from fastapi import APIRouter, Query, Depends
from app.models.audit import AuditRepository, get_audit_repository

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/", summary="List recent audit records")
async def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    """Return the most recent audit log entries."""
    records = await audit_repo.find_recent(limit=limit)
    return {"audit_logs": records, "count": len(records)}


@router.get("/{target}", summary="Audit records for a target")
async def get_audit_for_target(
    target: str,
    limit: int = Query(default=100, ge=1, le=500),
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    """Return audit records for a specific target (e.g., a device_id)."""
    records = await audit_repo.find_by_target(target, limit=limit)
    return {"target": target, "audit_logs": records, "count": len(records)}
