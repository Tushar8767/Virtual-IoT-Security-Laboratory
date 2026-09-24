"""
Security Events API Router — Phase 0 Skeleton
Full implementation in Phase 7.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/security", tags=["Security"])


@router.get("/events", summary="List security events [Phase 7]")
async def list_security_events():
    return {"events": [], "message": "Security engine implemented in Phase 7"}


@router.get("/alerts", summary="List alerts [Phase 7]")
async def list_alerts():
    return {"alerts": [], "message": "Alert system implemented in Phase 7"}
