"""
Security API Router — Events, Alerts & SOC Metrics

Endpoints:
    GET   /api/security/events             — list security events
    GET   /api/security/alerts             — list security alerts
    PATCH /api/security/alerts/{alert_id}  — update alert status (ACTIVE/RESOLVED)
    GET   /api/security/summary            — SOC metrics summary
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, Depends, HTTPException, Body, status
from app.repositories.security_repository import SecurityRepository, get_security_repository

router = APIRouter(prefix="/security", tags=["Security"])


@router.get("/events", summary="List detected security events")
async def list_security_events(
    limit: int = Query(default=50, ge=1, le=200),
    device_id: Optional[str] = None,
    repo: SecurityRepository = Depends(get_security_repository),
):
    """Retrieve security events detected by the rules engine."""
    events = await repo.find_recent_events(limit=limit, device_id=device_id)
    return {"count": len(events), "events": events}


@router.get("/alerts", summary="List security alerts")
async def list_security_alerts(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    severity: Optional[str] = None,
    device_id: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    repo: SecurityRepository = Depends(get_security_repository),
):
    """Retrieve security alerts requiring investigation."""
    alerts = await repo.find_alerts(
        status=status_filter,
        severity=severity,
        device_id=device_id,
        limit=limit,
    )
    return {"count": len(alerts), "alerts": alerts}


@router.patch("/alerts/{alert_id}", summary="Update alert triage status")
async def update_alert_status(
    alert_id: str,
    new_status: str = Body(..., embed=True, examples=["INVESTIGATING", "RESOLVED", "DISMISSED"]),
    repo: SecurityRepository = Depends(get_security_repository),
):
    """Change the status of an alert during an investigation."""
    updated = await repo.update_alert_status(alert_id, new_status.upper())
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert '{alert_id}' not found")
    return updated


@router.get("/summary", summary="Get SOC security summary counts")
async def get_security_summary(
    repo: SecurityRepository = Depends(get_security_repository),
):
    """Get active alerts count, total events, and incident overview."""
    return await repo.get_security_summary()