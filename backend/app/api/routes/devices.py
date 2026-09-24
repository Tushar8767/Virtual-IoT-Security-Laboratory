"""
Devices API Router — Phase 1 Full Implementation

Endpoints:
    GET    /api/devices                   — list devices
    POST   /api/devices                   — create device
    GET    /api/devices/summary           — status summary counts
    GET    /api/devices/{device_id}       — get device
    PATCH  /api/devices/{device_id}       — update device
    POST   /api/devices/{device_id}/provision   — provision device
    POST   /api/devices/{device_id}/rotate      — rotate credentials
    POST   /api/devices/{device_id}/suspend     — suspend device
    POST   /api/devices/{device_id}/reinstate   — reinstate device
    POST   /api/devices/{device_id}/revoke      — revoke device
"""

import structlog
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Body, Depends, status

from app.schemas.device import (
    DeviceCreateRequest,
    DeviceUpdateRequest,
    DeviceResponse,
    DeviceListResponse,
    DeviceProvisionResponse,
    DeviceStatusSummary,
)
from app.services.device_service import (
    DeviceService,
    DeviceNotFoundError,
    InvalidStateTransitionError,
    DeviceAlreadyProvisionedError,
    get_device_service,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/devices", tags=["Devices"])


# ============================================================
# Helpers
# ============================================================

def _not_found(device_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Device '{device_id}' not found",
    )


def _bad_transition(msg: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=msg,
    )


# ============================================================
# Routes
# ============================================================

@router.get(
    "/summary",
    response_model=DeviceStatusSummary,
    summary="Get device status summary counts",
)
async def get_device_summary(
    svc: DeviceService = Depends(get_device_service),
):
    """Return counts of devices grouped by status."""
    return await svc.get_status_summary()


@router.get(
    "/",
    response_model=DeviceListResponse,
    summary="List all devices",
)
async def list_devices(
    status_filter: Optional[str] = Query(
        default=None,
        alias="status",
        description="Filter by device status (REGISTERED, ONLINE, OFFLINE, etc.)",
    ),
    device_type: Optional[str] = Query(
        default=None,
        description="Filter by device type",
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=200, description="Results per page"),
    svc: DeviceService = Depends(get_device_service),
):
    """
    List simulated devices with optional filtering and pagination.

    Use the `status` query parameter to filter by lifecycle state.
    Use the `device_type` parameter to filter by device type.
    """
    return await svc.list_devices(
        status=status_filter,
        device_type=device_type,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new simulated device",
)
async def create_device(
    request: DeviceCreateRequest,
    svc: DeviceService = Depends(get_device_service),
):
    """
    Create a new virtual device in REGISTERED state.

    The device is not yet provisioned — it has no credentials and cannot
    communicate until provisioned via `POST /api/devices/{id}/provision`.

    Default capabilities are assigned based on device type unless overridden.
    """
    device = await svc.create_device(request)
    logger.info("api_device_created", device_id=device.device_id)
    return device


@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Get device by ID",
)
async def get_device(
    device_id: str,
    svc: DeviceService = Depends(get_device_service),
):
    """Get full details of a specific simulated device."""
    try:
        return await svc.get_device(device_id)
    except DeviceNotFoundError:
        raise _not_found(device_id)


@router.patch(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Update device fields",
)
async def update_device(
    device_id: str,
    request: DeviceUpdateRequest,
    svc: DeviceService = Depends(get_device_service),
):
    """
    Update mutable fields on a device.
    Cannot change device status via this endpoint — use dedicated endpoints.
    Cannot update a REVOKED device.
    """
    try:
        return await svc.update_device(device_id, request)
    except DeviceNotFoundError:
        raise _not_found(device_id)
    except InvalidStateTransitionError as e:
        raise _bad_transition(str(e))


@router.post(
    "/{device_id}/provision",
    response_model=DeviceProvisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Provision a device and issue credentials",
)
async def provision_device(
    device_id: str,
    svc: DeviceService = Depends(get_device_service),
):
    """
    Provision a REGISTERED device.

    Generates a device API key and transitions the device to PROVISIONED state.

    **Important:** The `plain_key` in the response is shown ONLY ONCE.
    Store it securely — it cannot be retrieved again.
    Use `POST /api/devices/{id}/rotate` to issue new credentials.
    """
    try:
        return await svc.provision_device(device_id)
    except DeviceNotFoundError:
        raise _not_found(device_id)
    except DeviceAlreadyProvisionedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidStateTransitionError as e:
        raise _bad_transition(str(e))


@router.post(
    "/{device_id}/rotate",
    response_model=DeviceProvisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Rotate device credentials",
)
async def rotate_device_credentials(
    device_id: str,
    svc: DeviceService = Depends(get_device_service),
):
    """
    Rotate device credentials. The old key is immediately revoked.
    A new key is generated and returned once.
    """
    try:
        return await svc.rotate_credentials(device_id)
    except DeviceNotFoundError:
        raise _not_found(device_id)
    except InvalidStateTransitionError as e:
        raise _bad_transition(str(e))


@router.post(
    "/{device_id}/suspend",
    response_model=DeviceResponse,
    summary="Suspend a device",
)
async def suspend_device(
    device_id: str,
    reason: str = Body(default="", embed=True),
    svc: DeviceService = Depends(get_device_service),
):
    """
    Suspend a device (ONLINE or OFFLINE → SUSPENDED).
    A suspended device cannot communicate but can be reinstated.
    """
    try:
        return await svc.suspend_device(device_id, reason=reason)
    except DeviceNotFoundError:
        raise _not_found(device_id)
    except InvalidStateTransitionError as e:
        raise _bad_transition(str(e))


@router.post(
    "/{device_id}/reinstate",
    response_model=DeviceResponse,
    summary="Reinstate a suspended device",
)
async def reinstate_device(
    device_id: str,
    svc: DeviceService = Depends(get_device_service),
):
    """Reinstate a SUSPENDED device back to ONLINE state."""
    try:
        return await svc.reinstate_device(device_id)
    except DeviceNotFoundError:
        raise _not_found(device_id)
    except InvalidStateTransitionError as e:
        raise _bad_transition(str(e))


@router.post(
    "/{device_id}/revoke",
    response_model=DeviceResponse,
    summary="Revoke a device permanently",
)
async def revoke_device(
    device_id: str,
    reason: str = Body(default="", embed=True),
    svc: DeviceService = Depends(get_device_service),
):
    """
    Permanently revoke a device.

    **This action is irreversible.** The device is moved to REVOKED state
    and its credentials are invalidated. No further communication is accepted.
    """
    try:
        return await svc.revoke_device(device_id, reason=reason)
    except DeviceNotFoundError:
        raise _not_found(device_id)
    except InvalidStateTransitionError as e:
        raise _bad_transition(str(e))
