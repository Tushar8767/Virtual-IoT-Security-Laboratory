"""
Device API Schemas — Pydantic v2

Request and response schemas for device API endpoints.
These are the public API shapes — separate from the internal domain models.

Design rule: never expose credential hashes in API responses.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.models.device import DeviceType, DeviceStatus, DeviceCapability, TrustState


# ============================================================
# Request Schemas
# ============================================================

class DeviceCreateRequest(BaseModel):
    """Schema for POST /api/devices — create a new device."""

    device_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Human-readable device name",
        examples=["Living Room Temp Sensor"],
    )
    device_type: DeviceType = Field(
        ...,
        description="Type of simulated device",
        examples=["temperature_sensor"],
    )
    firmware_version: str = Field(
        default="1.0.0",
        pattern=r"^\d+\.\d+\.\d+$",
        description="Firmware version string (semver format)",
    )
    description: str = Field(
        default="",
        max_length=500,
        description="Optional device description",
    )
    heartbeat_interval_seconds: int = Field(
        default=15,
        ge=5,
        le=300,
        description="Heartbeat interval in seconds (5–300)",
    )
    capabilities: Optional[List[DeviceCapability]] = Field(
        default=None,
        description="Override default capabilities. If not set, defaults for device type are used.",
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Optional free-form metadata (location, owner, tags, etc.)",
    )

    @field_validator("device_name")
    @classmethod
    def strip_device_name(cls, v: str) -> str:
        return v.strip()


class DeviceUpdateRequest(BaseModel):
    """Schema for PATCH /api/devices/{id} — update device fields."""

    device_name: Optional[str] = Field(
        default=None, min_length=1, max_length=100
    )
    firmware_version: Optional[str] = Field(
        default=None, pattern=r"^\d+\.\d+\.\d+$"
    )
    description: Optional[str] = Field(default=None, max_length=500)
    heartbeat_interval_seconds: Optional[int] = Field(default=None, ge=5, le=300)
    capabilities: Optional[List[DeviceCapability]] = None
    metadata: Optional[dict] = None


# ============================================================
# Response Schemas
# ============================================================

class DeviceCredentialResponse(BaseModel):
    """
    Credential info returned after provisioning.
    The plain_key is shown ONCE — it is not stored.
    """
    credential_id: str
    plain_key: str  # Only returned during provisioning — never stored
    created_at: datetime
    expires_at: Optional[datetime] = None
    message: str = "Store this key securely. It will not be shown again."


class DeviceResponse(BaseModel):
    """Full device response — all fields except credential hash."""

    device_id: str
    device_name: str
    device_type: str
    status: str
    trust_state: str
    firmware_version: str
    capabilities: List[str]
    description: str
    heartbeat_interval_seconds: int
    missed_heartbeats: int
    is_provisioned: bool
    created_at: datetime
    updated_at: datetime
    last_seen: Optional[datetime]
    provisioned_at: Optional[datetime]
    metadata: dict

    @classmethod
    def from_document(cls, doc: dict) -> "DeviceResponse":
        """Build a DeviceResponse from a MongoDB document."""
        return cls(
            device_id=doc["device_id"],
            device_name=doc["device_name"],
            device_type=doc["device_type"],
            status=doc["status"],
            trust_state=doc.get("trust_state", "UNTRUSTED"),
            firmware_version=doc.get("firmware_version", "1.0.0"),
            capabilities=doc.get("capabilities", []),
            description=doc.get("description", ""),
            heartbeat_interval_seconds=doc.get("heartbeat_interval_seconds", 15),
            missed_heartbeats=doc.get("missed_heartbeats", 0),
            is_provisioned=doc.get("credential") is not None,
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
            last_seen=doc.get("last_seen"),
            provisioned_at=doc.get("provisioned_at"),
            metadata=doc.get("metadata", {}),
        )


class DeviceListResponse(BaseModel):
    """Paginated device list response."""
    devices: List[DeviceResponse]
    total: int
    page: int
    page_size: int


class DeviceProvisionResponse(BaseModel):
    """Response returned when a device is provisioned."""
    device: DeviceResponse
    credential: DeviceCredentialResponse


class DeviceStatusSummary(BaseModel):
    """Summary counts for the dashboard."""
    total: int
    registered: int
    provisioned: int
    online: int
    offline: int
    suspended: int
    revoked: int

