"""
Lab Control API Router — Orchestration, Start, Stop & Reset

Endpoints:
    GET  /api/lab/status — comprehensive status of all lab components
    POST /api/lab/start  — start the virtual simulation fleet
    POST /api/lab/stop   — pause the virtual simulation fleet
    POST /api/lab/reset  — reset the laboratory back to initial baseline
"""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
import structlog

from app.core.database import get_database_status, get_database
from app.core.mqtt_client import get_mqtt_status
from app.repositories.device_repository import DeviceRepository, get_device_repository
from app.repositories.security_repository import SecurityRepository, get_security_repository
from app.models.audit import AuditAction, AuditResult, AuditRepository, get_audit_repository
from device_simulator.simulator_manager import SimulatorManager
from app.telemetry.pipeline import TelemetryPipeline
from app.repositories.telemetry_repository import TelemetryRepository

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/lab", tags=["Lab Control"])

_active_simulator: SimulatorManager = SimulatorManager()


@router.get("/status", summary="Get comprehensive lab status")
async def get_lab_status(
    dev_repo: DeviceRepository = Depends(get_device_repository),
    sec_repo: SecurityRepository = Depends(get_security_repository),
):
    """Return status of all subsystems: backend, database, MQTT, simulation fleet, alerts."""
    db_status = await get_database_status()
    mqtt_status = get_mqtt_status()
    device_summary = await dev_repo.get_status_summary()
    security_summary = await sec_repo.get_security_summary()

    is_healthy = db_status.get("connected", False) and mqtt_status.get("connected", False)

    return {
        "lab_status": "READY" if is_healthy else "RUNNING_DEGRADED",
        "simulation": {
            "active_workers": _active_simulator.active_devices_count,
            "total_managed": _active_simulator.total_devices_count,
            "running": _active_simulator.active_devices_count > 0,
        },
        "fleet": device_summary,
        "security": security_summary,
        "services": {
            "database": db_status,
            "mqtt": mqtt_status,
        },
    }


@router.post("/start", summary="Start virtual device simulation fleet")
async def start_lab_simulation(
    dev_repo: DeviceRepository = Depends(get_device_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    """Spawns background simulation workers for all provisioned virtual devices."""
    global _active_simulator

    if _active_simulator.active_devices_count > 0:
        return {"status": "ALREADY_RUNNING", "active_workers": _active_simulator.active_devices_count}

    devices, total = await dev_repo.find_all(page=1, page_size=100)

    db = get_database()
    pipeline = TelemetryPipeline(TelemetryRepository(db), dev_repo)

    async def ingest_callback(payload):
        await pipeline.process_telemetry(payload)

    _active_simulator = SimulatorManager()

    for d in devices:
        _active_simulator.create_device_from_dict(d, on_telemetry_emit=ingest_callback)


    await _active_simulator.start_all()

    await audit_repo.log(
        action=AuditAction.LAB_STARTED,
        target="lab_simulation",
        result=AuditResult.SUCCESS,
        actor="operator",
        metadata={"started_workers": _active_simulator.active_devices_count},
    )

    logger.info("lab_simulation_started", workers=_active_simulator.active_devices_count)
    return {
        "status": "STARTED",
        "started_workers": _active_simulator.active_devices_count,
    }


@router.post("/stop", summary="Stop virtual device simulation fleet")
async def stop_lab_simulation(
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    """Cleanly pauses all background simulation workers."""
    global _active_simulator
    await _active_simulator.stop_all()

    await audit_repo.log(
        action=AuditAction.LAB_STOPPED,
        target="lab_simulation",
        result=AuditResult.SUCCESS,
        actor="operator",
    )

    logger.info("lab_simulation_stopped")
    return {"status": "STOPPED"}


@router.post("/reset", summary="Reset lab state")
async def reset_lab_simulation(
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    """Resets simulator fleet back to initial clean state."""
    global _active_simulator
    await _active_simulator.stop_all()
    _active_simulator = SimulatorManager()

    await audit_repo.log(
        action=AuditAction.LAB_RESET,
        target="lab_simulation",
        result=AuditResult.SUCCESS,
        actor="operator",
    )

    logger.info("lab_reset_completed")
    return {"status": "RESET_SUCCESSFUL"}