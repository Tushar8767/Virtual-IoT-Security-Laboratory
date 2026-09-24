"""
Device Service — Business Logic Layer

Orchestrates:
- Device creation with ID generation
- State machine transitions
- Credential provisioning
- Device updates
- Audit logging for every state change
- WebSocket event broadcasting

This is the authoritative layer for device lifecycle decisions.
The API routes delegate here; the repository handles only persistence.
"""

import uuid
import structlog
from datetime import datetime, timezone
from typing import Optional

from app.models.device import (
    DeviceStatus,
    DeviceCapability,
    TrustState,
    DEFAULT_CAPABILITIES,
    is_valid_transition,
)
from app.models.audit import AuditAction, AuditResult, AuditRepository
from app.repositories.device_repository import DeviceRepository
from app.schemas.device import (
    DeviceCreateRequest,
    DeviceUpdateRequest,
    DeviceResponse,
    DeviceProvisionResponse,
    DeviceCredentialResponse,
    DeviceListResponse,
    DeviceStatusSummary,
)
from app.core.security import (
    generate_device_credential_pair,
    generate_correlation_id,
    hash_credential,
)

logger = structlog.get_logger(__name__)


class DeviceNotFoundError(Exception):
    """Raised when a device_id does not exist."""
    pass


class InvalidStateTransitionError(Exception):
    """Raised when a requested state transition is not allowed."""
    pass


class DeviceAlreadyProvisionedError(Exception):
    """Raised when trying to provision an already-provisioned device."""
    pass


class DeviceService:
    """
    Device service — all business logic for the device domain.
    Receives repository and audit_repo via dependency injection.
    """

    def __init__(
        self,
        device_repo: DeviceRepository,
        audit_repo: AuditRepository,
    ):
        self.device_repo = device_repo
        self.audit_repo = audit_repo

    # ----------------------------------------------------------
    # Create
    # ----------------------------------------------------------

    async def create_device(
        self,
        request: DeviceCreateRequest,
        actor: str = "api",
    ) -> DeviceResponse:
        """
        Create a new device in REGISTERED state.
        Assigns default capabilities for the device type.
        """
        correlation_id = generate_correlation_id()
        device_id = f"dev-{uuid.uuid4().hex[:12]}"

        # Determine capabilities
        caps = request.capabilities
        if caps is None:
            caps = DEFAULT_CAPABILITIES.get(request.device_type, [])

        now = datetime.now(timezone.utc)
        document = {
            "device_id": device_id,
            "device_name": request.device_name,
            "device_type": request.device_type.value,
            "status": DeviceStatus.REGISTERED.value,
            "trust_state": TrustState.UNTRUSTED.value,
            "firmware_version": request.firmware_version,
            "capabilities": [c.value if hasattr(c, "value") else c for c in caps],
            "description": request.description,
            "heartbeat_interval_seconds": request.heartbeat_interval_seconds,
            "missed_heartbeats": 0,
            "credential": None,
            "created_at": now,
            "updated_at": now,
            "last_seen": None,
            "provisioned_at": None,
            "metadata": request.metadata,
        }

        doc = await self.device_repo.insert(document)

        # Audit log
        await self.audit_repo.log(
            action=AuditAction.DEVICE_CREATED,
            target=device_id,
            result=AuditResult.SUCCESS,
            actor=actor,
            correlation_id=correlation_id,
            metadata={
                "device_name": request.device_name,
                "device_type": request.device_type.value,
                "firmware_version": request.firmware_version,
            },
        )

        logger.info(
            "device_created",
            device_id=device_id,
            device_type=request.device_type.value,
            correlation_id=correlation_id,
        )

        # Broadcast WebSocket event
        await self._broadcast("device_status_changed", {
            "device_id": device_id,
            "status": DeviceStatus.REGISTERED.value,
            "event": "device_created",
            "correlation_id": correlation_id,
        })

        return DeviceResponse.from_document(doc)

    # ----------------------------------------------------------
    # Read
    # ----------------------------------------------------------

    async def get_device(self, device_id: str) -> DeviceResponse:
        """Get a device by ID. Raises DeviceNotFoundError if missing."""
        doc = await self.device_repo.find_by_id(device_id)
        if not doc:
            raise DeviceNotFoundError(f"Device '{device_id}' not found")
        return DeviceResponse.from_document(doc)

    async def list_devices(
        self,
        status: Optional[str] = None,
        device_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> DeviceListResponse:
        """List devices with optional filters and pagination."""
        documents, total = await self.device_repo.find_all(
            status=status,
            device_type=device_type,
            page=page,
            page_size=page_size,
        )
        return DeviceListResponse(
            devices=[DeviceResponse.from_document(d) for d in documents],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_status_summary(self) -> DeviceStatusSummary:
        """Get device count summary by status."""
        summary = await self.device_repo.get_status_summary()
        return DeviceStatusSummary(**summary)

    # ----------------------------------------------------------
    # Update
    # ----------------------------------------------------------

    async def update_device(
        self,
        device_id: str,
        request: DeviceUpdateRequest,
        actor: str = "api",
    ) -> DeviceResponse:
        """Update mutable device fields. Cannot change status via this method."""
        doc = await self.device_repo.find_by_id(device_id)
        if not doc:
            raise DeviceNotFoundError(f"Device '{device_id}' not found")

        # Reject updates to REVOKED devices
        if doc["status"] == DeviceStatus.REVOKED.value:
            raise InvalidStateTransitionError(
                "Cannot update a REVOKED device"
            )

        fields: dict = {}
        if request.device_name is not None:
            fields["device_name"] = request.device_name
        if request.firmware_version is not None:
            fields["firmware_version"] = request.firmware_version
        if request.description is not None:
            fields["description"] = request.description
        if request.heartbeat_interval_seconds is not None:
            fields["heartbeat_interval_seconds"] = request.heartbeat_interval_seconds
        if request.capabilities is not None:
            fields["capabilities"] = [
                c.value if hasattr(c, "value") else c for c in request.capabilities
            ]
        if request.metadata is not None:
            fields["metadata"] = request.metadata

        if not fields:
            # Nothing to update — return current state
            return DeviceResponse.from_document(doc)

        updated = await self.device_repo.update_fields(device_id, fields)

        await self.audit_repo.log(
            action=AuditAction.DEVICE_UPDATED,
            target=device_id,
            result=AuditResult.SUCCESS,
            actor=actor,
            metadata={"updated_fields": list(fields.keys())},
        )

        logger.info("device_updated", device_id=device_id, fields=list(fields.keys()))
        return DeviceResponse.from_document(updated)

    # ----------------------------------------------------------
    # Provisioning
    # ----------------------------------------------------------

    async def provision_device(
        self,
        device_id: str,
        actor: str = "api",
    ) -> DeviceProvisionResponse:
        """
        Provision a REGISTERED device.

        Generates a device API key (plain + hashed).
        Only the hashed key is stored — the plain key is returned once.
        Transitions device: REGISTERED → PROVISIONED.
        """
        doc = await self.device_repo.find_by_id(device_id)
        if not doc:
            raise DeviceNotFoundError(f"Device '{device_id}' not found")

        if doc.get("credential") is not None and not doc["credential"].get("is_revoked", False):
            raise DeviceAlreadyProvisionedError(
                f"Device '{device_id}' is already provisioned. "
                "Rotate credentials instead."
            )

        current_status = DeviceStatus(doc["status"])
        target_status = DeviceStatus.PROVISIONED

        if not is_valid_transition(current_status, target_status):
            raise InvalidStateTransitionError(
                f"Cannot provision device in {current_status.value} state. "
                f"Valid transitions from {current_status.value}: "
                f"{[s.value for s in [target_status]]}"
            )

        correlation_id = generate_correlation_id()

        # Generate credential pair
        plain_key, hashed_key = generate_device_credential_pair()
        credential_id = f"cred-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        credential_doc = {
            "credential_id": credential_id,
            "hashed_key": hashed_key,
            "created_at": now,
            "expires_at": None,
            "is_revoked": False,
        }

        # Store credential and update status
        await self.device_repo.set_credential(device_id, credential_doc)
        updated = await self.device_repo.update_status(device_id, target_status.value)

        await self.audit_repo.log(
            action=AuditAction.DEVICE_PROVISIONED,
            target=device_id,
            result=AuditResult.SUCCESS,
            actor=actor,
            correlation_id=correlation_id,
            metadata={"credential_id": credential_id},
        )

        logger.info(
            "device_provisioned",
            device_id=device_id,
            credential_id=credential_id,
            correlation_id=correlation_id,
        )

        await self._broadcast("device_status_changed", {
            "device_id": device_id,
            "status": target_status.value,
            "event": "device_provisioned",
            "correlation_id": correlation_id,
        })

        return DeviceProvisionResponse(
            device=DeviceResponse.from_document(updated),
            credential=DeviceCredentialResponse(
                credential_id=credential_id,
                plain_key=plain_key,
                created_at=now,
                expires_at=None,
            ),
        )

    async def rotate_credentials(
        self,
        device_id: str,
        actor: str = "api",
    ) -> DeviceProvisionResponse:
        """
        Rotate device credentials.
        Revokes old credential and issues a new one.
        """
        doc = await self.device_repo.find_by_id(device_id)
        if not doc:
            raise DeviceNotFoundError(f"Device '{device_id}' not found")

        if doc["status"] in (DeviceStatus.REVOKED.value,):
            raise InvalidStateTransitionError(
                "Cannot rotate credentials for a REVOKED device"
            )

        correlation_id = generate_correlation_id()
        plain_key, hashed_key = generate_device_credential_pair()
        credential_id = f"cred-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        credential_doc = {
            "credential_id": credential_id,
            "hashed_key": hashed_key,
            "created_at": now,
            "expires_at": None,
            "is_revoked": False,
        }

        updated = await self.device_repo.set_credential(device_id, credential_doc)

        await self.audit_repo.log(
            action=AuditAction.CREDENTIAL_ROTATED,
            target=device_id,
            result=AuditResult.SUCCESS,
            actor=actor,
            correlation_id=correlation_id,
            metadata={"new_credential_id": credential_id},
        )

        logger.info(
            "credential_rotated",
            device_id=device_id,
            credential_id=credential_id,
            correlation_id=correlation_id,
        )

        return DeviceProvisionResponse(
            device=DeviceResponse.from_document(updated),
            credential=DeviceCredentialResponse(
                credential_id=credential_id,
                plain_key=plain_key,
                created_at=now,
            ),
        )

    # ----------------------------------------------------------
    # State Transitions
    # ----------------------------------------------------------

    async def suspend_device(
        self,
        device_id: str,
        reason: str = "",
        actor: str = "api",
    ) -> DeviceResponse:
        """Suspend a device (ONLINE or OFFLINE → SUSPENDED)."""
        return await self._transition(
            device_id=device_id,
            target=DeviceStatus.SUSPENDED,
            action=AuditAction.DEVICE_SUSPENDED,
            event_name="device_suspended",
            actor=actor,
            metadata={"reason": reason} if reason else {},
        )

    async def reinstate_device(
        self,
        device_id: str,
        actor: str = "api",
    ) -> DeviceResponse:
        """Reinstate a SUSPENDED device back to ONLINE."""
        return await self._transition(
            device_id=device_id,
            target=DeviceStatus.ONLINE,
            action=AuditAction.DEVICE_REINSTATED,
            event_name="device_reinstated",
            actor=actor,
        )

    async def revoke_device(
        self,
        device_id: str,
        reason: str = "",
        actor: str = "api",
    ) -> DeviceResponse:
        """
        Revoke a device (terminal state — no recovery).
        Also revokes the device credential.
        """
        response = await self._transition(
            device_id=device_id,
            target=DeviceStatus.REVOKED,
            action=AuditAction.DEVICE_REVOKED,
            event_name="device_revoked",
            actor=actor,
            metadata={"reason": reason} if reason else {},
        )

        # Also revoke the credential
        await self.device_repo.revoke_credential(device_id)
        await self.audit_repo.log(
            action=AuditAction.CREDENTIAL_REVOKED,
            target=device_id,
            result=AuditResult.SUCCESS,
            actor=actor,
            metadata={"reason": "device_revoked"},
        )

        return response

    async def mark_online(self, device_id: str) -> DeviceResponse:
        """Mark a device as ONLINE (called on heartbeat/connection)."""
        return await self._transition(
            device_id=device_id,
            target=DeviceStatus.ONLINE,
            action=AuditAction.DEVICE_UPDATED,
            event_name="device_online",
            actor="system",
        )

    async def mark_offline(self, device_id: str) -> DeviceResponse:
        """Mark a device as OFFLINE (called on heartbeat timeout)."""
        return await self._transition(
            device_id=device_id,
            target=DeviceStatus.OFFLINE,
            action=AuditAction.DEVICE_UPDATED,
            event_name="device_offline",
            actor="system",
        )

    # ----------------------------------------------------------
    # Authentication Support
    # ----------------------------------------------------------

    async def get_hashed_credential(self, device_id: str) -> Optional[str]:
        """
        Return the stored hashed credential for a device.
        Used by the authentication layer to verify device API keys.
        This is the ONLY path that accesses the hashed credential.
        """
        doc = await self.device_repo.find_by_id(device_id)
        if not doc or not doc.get("credential"):
            return None
        if doc["credential"].get("is_revoked", False):
            return None
        return doc["credential"]["hashed_key"]

    # ----------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------

    async def _transition(
        self,
        device_id: str,
        target: DeviceStatus,
        action: AuditAction,
        event_name: str,
        actor: str,
        metadata: Optional[dict] = None,
    ) -> DeviceResponse:
        """
        Internal state transition helper.
        Validates the transition, updates the DB, logs audit, broadcasts WS event.
        """
        doc = await self.device_repo.find_by_id(device_id)
        if not doc:
            raise DeviceNotFoundError(f"Device '{device_id}' not found")

        current = DeviceStatus(doc["status"])

        if not is_valid_transition(current, target):
            raise InvalidStateTransitionError(
                f"Invalid transition: {current.value} → {target.value} "
                f"for device '{device_id}'"
            )

        correlation_id = generate_correlation_id()
        updated = await self.device_repo.update_status(device_id, target.value)

        await self.audit_repo.log(
            action=action,
            target=device_id,
            result=AuditResult.SUCCESS,
            actor=actor,
            correlation_id=correlation_id,
            metadata=metadata or {},
        )

        logger.info(
            "device_state_transition",
            device_id=device_id,
            from_status=current.value,
            to_status=target.value,
            actor=actor,
            correlation_id=correlation_id,
        )

        await self._broadcast("device_status_changed", {
            "device_id": device_id,
            "from_status": current.value,
            "status": target.value,
            "event": event_name,
            "correlation_id": correlation_id,
        })

        return DeviceResponse.from_document(updated)

    async def _broadcast(self, event_type: str, data: dict) -> None:
        """Broadcast a WebSocket event. Silently skips if WS not available."""
        try:
            from app.api.websocket import broadcast_event
            await broadcast_event(event_type, data)
        except Exception as e:
            logger.debug("ws_broadcast_failed", error=str(e))


def get_device_service() -> DeviceService:
    """
    FastAPI dependency — returns a DeviceService instance.
    Repositories are constructed with the active database connection.
    """
    from app.core.database import get_database
    db = get_database()
    return DeviceService(
        device_repo=DeviceRepository(db),
        audit_repo=AuditRepository(db),
    )
