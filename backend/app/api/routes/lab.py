"""
Lab Control API Router

Provides start/stop/reset/status endpoints for the lab.
Status is functional in Phase 0; full control in Phase 2+.
"""
import structlog
from fastapi import APIRouter
from app.core.config import settings
from app.core.database import get_database_status
from app.core.mqtt_client import get_mqtt_status

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/lab", tags=["Lab"])


@router.get("/status", summary="Get lab status")
async def get_lab_status():
    """
    Returns the current status of all lab services.
    """
    db_status = await get_database_status()
    mqtt_status = get_mqtt_status()

    services_healthy = db_status["connected"] and mqtt_status["connected"]

    return {
        "lab_status": "running" if services_healthy else "degraded",
        "version": settings.APP_VERSION,
        "services": {
            "database": db_status,
            "mqtt_broker": mqtt_status,
        },
        "simulation": {
            "active_devices": 0,
            "active_scenarios": 0,
            "note": "Simulation engine implemented in Phase 2",
        },
    }


@router.post("/start", summary="Start the lab [Phase 2]")
async def start_lab():
    return {"status": "accepted", "message": "Lab start implemented in Phase 2"}


@router.post("/stop", summary="Stop the lab [Phase 2]")
async def stop_lab():
    return {"status": "accepted", "message": "Lab stop implemented in Phase 2"}


@router.post("/reset", summary="Reset the lab [Phase 2]")
async def reset_lab():
    return {"status": "accepted", "message": "Lab reset implemented in Phase 2"}

