"""
Device Domain Models

Defines the core Device entity and related enums.
These are the internal domain models — not the API schemas.
"""

from enum import Enum
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# Enums
# ============================================================

class DeviceType(str, Enum):
    """Supported simulated device types."""
    TEMPERATURE_SENSOR = "temperature_sensor"
    MOTION_SENSOR = "motion_sensor"
    ENVIRONMENTAL_SENSOR = "environmental_sensor"
    SMART_ACTUATOR = "smart_actuator"
    GATEWAY = "gateway"
    INDUSTRIAL_CONTROLLER = "industrial_controller"


class DeviceStatus(str, Enum):
    """
    Device lifecycle states.

    Valid transitions:
        REGISTERED  → PROVISIONED
        PROVISIONED → ONLINE
        ONLINE      → OFFLINE
        OFFLINE     → ONLINE
        ONLINE      → SUSPENDED
        OFFLINE     → SUSPENDED
        SUSPENDED   → ONLINE (reinstate)
        SUSPENDED   → REVOKED
        ONLINE      → REVOKED
        OFFLINE     → REVOKED
        PROVISIONED → REVOKED
    """
    REGISTERED = "REGISTERED"
    PROVISIONED = "PROVISIONED"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


class DeviceCapability(str, Enum):
    """
    Device capabilities used for authorization.
    Each device has a specific set of allowed capabilities.
    """
    READ_TELEMETRY = "READ_TELEMETRY"
    SEND_TELEMETRY = "SEND_TELEMETRY"
    RECEIVE_COMMANDS = "RECEIVE_COMMANDS"
    CONTROL_ACTUATOR = "CONTROL_ACTUATOR"
    CONFIGURE_DEVICE = "CONFIGURE_DEVICE"
    MANAGE_DEVICES = "MANAGE_DEVICES"


class TrustState(str, Enum):
    """Device trust state — separate from lifecycle status."""
    TRUSTED = "TRUSTED"
    UNTRUSTED = "UNTRUSTED"
    COMPROMISED = "COMPROMISED"


# ============================================================
# State Machine
# ============================================================

# Valid state transitions — enforced by the state machine
VALID_TRANSITIONS: dict[DeviceStatus, set[DeviceStatus]] = {
    DeviceStatus.REGISTERED:   {DeviceStatus.PROVISIONED, DeviceStatus.REVOKED},
    DeviceStatus.PROVISIONED:  {DeviceStatus.ONLINE, DeviceStatus.REVOKED},
    DeviceStatus.ONLINE:       {DeviceStatus.OFFLINE, DeviceStatus.SUSPENDED, DeviceStatus.REVOKED},
    DeviceStatus.OFFLINE:      {DeviceStatus.ONLINE, DeviceStatus.SUSPENDED, DeviceStatus.REVOKED},
    DeviceStatus.SUSPENDED:    {DeviceStatus.ONLINE, DeviceStatus.REVOKED},
    DeviceStatus.REVOKED:      set(),  # Terminal state — no transitions allowed
}

# Default capabilities per device type
DEFAULT_CAPABILITIES: dict[DeviceType, List[DeviceCapability]] = {
    DeviceType.TEMPERATURE_SENSOR: [
        DeviceCapability.SEND_TELEMETRY,
        DeviceCapability.READ_TELEMETRY,
        DeviceCapability.RECEIVE_COMMANDS,
    ],
    DeviceType.MOTION_SENSOR: [
        DeviceCapability.SEND_TELEMETRY,
        DeviceCapability.READ_TELEMETRY,
        DeviceCapability.RECEIVE_COMMANDS,
    ],
    DeviceType.ENVIRONMENTAL_SENSOR: [
        DeviceCapability.SEND_TELEMETRY,
        DeviceCapability.READ_TELEMETRY,
        DeviceCapability.RECEIVE_COMMANDS,
    ],
    DeviceType.SMART_ACTUATOR: [
        DeviceCapability.SEND_TELEMETRY,
        DeviceCapability.READ_TELEMETRY,
        DeviceCapability.RECEIVE_COMMANDS,
        DeviceCapability.CONTROL_ACTUATOR,
    ],
    DeviceType.GATEWAY: [
        DeviceCapability.SEND_TELEMETRY,
        DeviceCapability.READ_TELEMETRY,
        DeviceCapability.RECEIVE_COMMANDS,
        DeviceCapability.MANAGE_DEVICES,
    ],
    DeviceType.INDUSTRIAL_CONTROLLER: [
        DeviceCapability.SEND_TELEMETRY,
        DeviceCapability.READ_TELEMETRY,
        DeviceCapability.RECEIVE_COMMANDS,
        DeviceCapability.CONTROL_ACTUATOR,
        DeviceCapability.CONFIGURE_DEVICE,
    ],
}


def is_valid_transition(current: DeviceStatus, target: DeviceStatus) -> bool:
    """
    Check whether a state transition is valid.
    Returns True if the transition is allowed.
    """
    return target in VALID_TRANSITIONS.get(current, set())


# ============================================================
# Device Domain Model
# ============================================================

class DeviceCredential(BaseModel):
    """
    Device credential record.
    Only the hashed key is stored — the plain key is shown once at provisioning.
    """
    credential_id: str
    hashed_key: str  # bcrypt hash — never returned in API responses
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_revoked: bool = False


class Device(BaseModel):
    """
    Core device domain entity.

    Represents a simulated IoT device in the lab.
    This is NOT a real hardware device — it is a software simulation profile.
    """
    # Identity
    device_id: str
    device_name: str
    device_type: DeviceType

    # State
    status: DeviceStatus = DeviceStatus.REGISTERED
    trust_state: TrustState = TrustState.UNTRUSTED

    # Firmware
    firmware_version: str = "1.0.0"

    # Capabilities (authorization)
    capabilities: List[DeviceCapability] = Field(default_factory=list)

    # Credentials
    credential: Optional[DeviceCredential] = None

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: Optional[datetime] = None
    provisioned_at: Optional[datetime] = None

    # Heartbeat tracking
    heartbeat_interval_seconds: int = 15
    missed_heartbeats: int = 0

    # Metadata
    metadata: dict = Field(default_factory=dict)
    description: str = ""

    model_config = ConfigDict(use_enum_values=True)

    def can_transition_to(self, target: DeviceStatus) -> bool:
        """Check if this device can transition to the target status."""
        return is_valid_transition(self.status, target)

    def has_capability(self, capability: DeviceCapability) -> bool:
        """Check if this device has a specific capability."""
        return capability in self.capabilities or capability.value in self.capabilities
