"""
Authentication & Capability-Based Authorization — Security Boundary

Provides:
- Device API Key verification (bcrypt check against stored hash)
- Dependency guards: get_authenticated_device
- Capability enforcement: require_capability(DeviceCapability)
- Audit logging of AUTH_FAILURE and AUTHZ_FAILURE
"""

from typing import Optional, Dict, Any, Callable
from fastapi import Header, HTTPException, Depends, status
import structlog

from app.core.security import verify_credential, safe_string_compare
from app.models.device import DeviceCapability, DeviceStatus
from app.models.audit import AuditAction, AuditResult, AuditRepository, get_audit_repository
from app.repositories.device_repository import DeviceRepository, get_device_repository

logger = structlog.get_logger(__name__)


async def authenticate_device(
    x_device_id: Optional[str] = Header(None, alias="X-Device-Id"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    device_repo: DeviceRepository = Depends(get_device_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
) -> Dict[str, Any]:
    """
    FastAPI dependency validating device credentials.
    Returns the authenticated device document.
    """
    if not x_device_id or not x_api_key:
        logger.warning("auth_missing_credentials", device_id=x_device_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Device-Id or X-API-Key headers",
        )

    device = await device_repo.find_by_id(x_device_id)
    if not device:
        await audit_repo.log(
            action=AuditAction.AUTH_FAILURE,
            target=x_device_id,
            result=AuditResult.FAILURE,
            actor=x_device_id,
            metadata={"reason": "UNKNOWN_DEVICE"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device credentials",
        )

    # Check status
    if device.get("status") in (DeviceStatus.REVOKED.value, DeviceStatus.SUSPENDED.value):
        await audit_repo.log(
            action=AuditAction.AUTH_FAILURE,
            target=x_device_id,
            result=AuditResult.FAILURE,
            actor=x_device_id,
            metadata={"reason": f"DEVICE_{device.get('status')}"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Device is {device.get('status')}",
        )

    credential = device.get("credential")
    if not credential or credential.get("is_revoked", False):
        await audit_repo.log(
            action=AuditAction.AUTH_FAILURE,
            target=x_device_id,
            result=AuditResult.FAILURE,
            actor=x_device_id,
            metadata={"reason": "NO_ACTIVE_CREDENTIAL"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device credential is not active",
        )

    hashed_key = credential.get("hashed_key", "")
    is_valid = verify_credential(x_api_key, hashed_key)

    if not is_valid:
        await audit_repo.log(
            action=AuditAction.AUTH_FAILURE,
            target=x_device_id,
            result=AuditResult.FAILURE,
            actor=x_device_id,
            metadata={"reason": "INVALID_KEY"},
        )
        logger.warning("auth_failed_invalid_key", device_id=x_device_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device credentials",
        )

    # Auth success
    await audit_repo.log(
        action=AuditAction.AUTH_SUCCESS,
        target=x_device_id,
        result=AuditResult.SUCCESS,
        actor=x_device_id,
    )
    return device


def require_capability(required: DeviceCapability) -> Callable:
    """
    Factory creating a dependency enforcing a specific capability.
    """
    async def capability_checker(
        device: Dict[str, Any] = Depends(authenticate_device),
        audit_repo: AuditRepository = Depends(get_audit_repository),
    ) -> Dict[str, Any]:
        device_caps = device.get("capabilities", [])
        cap_val = required.value if hasattr(required, "value") else str(required)

        if cap_val not in device_caps:
            device_id = device.get("device_id", "UNKNOWN")
            logger.warning(
                "authorization_failed_missing_capability",
                device_id=device_id,
                required=cap_val,
                actual=device_caps,
            )
            await audit_repo.log(
                action=AuditAction.AUTHZ_FAILURE,
                target=device_id,
                result=AuditResult.FAILURE,
                actor=device_id,
                metadata={"required_capability": cap_val, "device_capabilities": device_caps},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Device lacks required capability: {cap_val}",
            )
        return device

    return capability_checker