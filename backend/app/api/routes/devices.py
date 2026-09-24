"""
Devices API Router — Phase 0 Skeleton

Full implementation in Phase 1 (Device Domain).
Provides skeleton endpoints so the app starts without errors.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("/", summary="List all devices [Phase 1]")
async def list_devices():
    return {"devices": [], "message": "Device Registry implemented in Phase 1"}


@router.get("/{device_id}", summary="Get device by ID [Phase 1]")
async def get_device(device_id: str):
    return {"device_id": device_id, "message": "Device detail implemented in Phase 1"}
