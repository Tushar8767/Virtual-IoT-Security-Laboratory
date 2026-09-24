"""
Security Domain Models

Defines models for:
- Security Events (raw detected anomalies or policy violations)
- Security Alerts (escalated incidents requiring investigation)
- Severities & Rule Types
"""

from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class RuleType(str, Enum):
    AUTH_FAILURE_FLOOD = "AUTH_FAILURE_FLOOD"
    TELEMETRY_RATE_ANOMALY = "TELEMETRY_RATE_ANOMALY"
    VALUE_OUT_OF_BOUNDS = "VALUE_OUT_OF_BOUNDS"
    HEARTBEAT_TIMEOUT = "HEARTBEAT_TIMEOUT"
    DEVICE_IMPERSONATION = "DEVICE_IMPERSONATION"
    UNAUTHORIZED_COMMAND = "UNAUTHORIZED_COMMAND"
    SUSPICIOUS_PAYLOAD = "SUSPICIOUS_PAYLOAD"


class SecurityEvent(BaseModel):
    """Raw detected security incident."""
    event_id: str
    rule_type: RuleType
    severity: Severity
    device_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    description: str
    correlation_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)


class SecurityAlert(BaseModel):
    """Escalated security alert displayed on SOC dashboard."""
    alert_id: str
    title: str
    rule_type: RuleType
    severity: Severity
    status: AlertStatus = AlertStatus.ACTIVE
    device_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: str
    event_ids: list[str] = Field(default_factory=list)
    description: str
    recommended_action: str = "Inspect device status and recent telemetry."

    model_config = ConfigDict(use_enum_values=True)