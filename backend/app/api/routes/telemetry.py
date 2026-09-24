"""
Telemetry API Router — Phase 0 Skeleton
Full implementation in Phase 4.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.get("/", summary="List telemetry [Phase 4]")
async def list_telemetry():
    return {"telemetry": [], "message": "Telemetry pipeline implemented in Phase 4"}

