"""
Investigation API Router

Endpoints:
    GET /api/investigation/device/{device_id}          — device forensic history
    GET /api/investigation/timeline/{correlation_id}   — correlated incident timeline
"""

from fastapi import APIRouter, HTTPException, Depends
from app.repositories.security_repository import SecurityRepository, get_security_repository
from app.repositories.telemetry_repository import TelemetryRepository, get_telemetry_repository
from app.repositories.device_repository import DeviceRepository, get_device_repository
from app.models.audit import AuditRepository, get_audit_repository
from app.services.investigation_service import InvestigationService

router = APIRouter(prefix="/investigation", tags=["Investigation"])


def get_investigation_service(
    sec_repo: SecurityRepository = Depends(get_security_repository),
    tel_repo: TelemetryRepository = Depends(get_telemetry_repository),
    dev_repo: DeviceRepository = Depends(get_device_repository),
    aud_repo: AuditRepository = Depends(get_audit_repository),
) -> InvestigationService:
    return InvestigationService(sec_repo, tel_repo, dev_repo, aud_repo)


@router.get("/device/{device_id}", summary="Get device forensic dossier")
async def get_device_forensic_profile(
    device_id: str,
    service: InvestigationService = Depends(get_investigation_service),
):
    """Retrieve full incident dossier for a device including events, alerts, and audit logs."""
    profile = await service.get_device_forensic_profile(device_id)
    if not profile["device"]:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    return profile


@router.get("/timeline/{correlation_id}", summary="Reconstruct incident timeline by correlation ID")
async def get_incident_timeline(
    correlation_id: str,
    service: InvestigationService = Depends(get_investigation_service),
):
    """Reconstruct unified chronological timeline of an incident using its correlation ID."""
    return await service.build_correlation_timeline(correlation_id)