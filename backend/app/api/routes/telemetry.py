"""
Telemetry API Router

Endpoints:
    GET  /api/telemetry/latest                — latest telemetry stream
    GET  /api/telemetry/device/{device_id}    — historical readings for a device
    POST /api/telemetry/ingest                — HTTP ingestion endpoint (e.g. for gateway/bridges)
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, Depends, HTTPException, status
from app.repositories.telemetry_repository import TelemetryRepository, get_telemetry_repository
from app.repositories.device_repository import DeviceRepository, get_device_repository
from app.telemetry.pipeline import TelemetryPipeline

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


def get_pipeline(
    t_repo: TelemetryRepository = Depends(get_telemetry_repository),
    d_repo: DeviceRepository = Depends(get_device_repository),
) -> TelemetryPipeline:
    return TelemetryPipeline(t_repo, d_repo)


@router.get("/", summary="List telemetry (compat)")
async def list_telemetry_root(
    limit: int = Query(default=50, ge=1, le=200),
    repo: TelemetryRepository = Depends(get_telemetry_repository),
):
    records = await repo.get_latest_fleet_telemetry(limit=limit)
    return {"count": len(records), "telemetry": records}


@router.get("/latest", summary="Get recent telemetry across all devices")
async def get_latest_telemetry(
    limit: int = Query(default=50, ge=1, le=200),
    repo: TelemetryRepository = Depends(get_telemetry_repository),
):
    """Retrieve the most recent telemetry readings across the simulated fleet."""
    records = await repo.get_latest_fleet_telemetry(limit=limit)
    return {"count": len(records), "telemetry": records}


@router.get("/device/{device_id}", summary="Get device telemetry history")
async def get_device_telemetry(
    device_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    repo: TelemetryRepository = Depends(get_telemetry_repository),
):
    """Retrieve historical telemetry entries for a specific device."""
    records = await repo.find_by_device(device_id, limit=limit)
    return {"device_id": device_id, "count": len(records), "telemetry": records}


@router.post("/ingest", summary="Ingest telemetry reading via HTTP", status_code=status.HTTP_201_CREATED)
async def ingest_telemetry(
    payload: Dict[str, Any],
    pipeline: TelemetryPipeline = Depends(get_pipeline),
):
    """
    Ingest a telemetry packet over HTTP (used by UART bridges or non-MQTT sources).
    """
    success, reason = await pipeline.process_telemetry(payload)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)
    return {"status": "INGESTED", "device_id": payload.get("device_id")}