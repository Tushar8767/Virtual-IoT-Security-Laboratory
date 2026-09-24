"""
Telemetry Domain Models

Defines the structure of stored telemetry records.
Every telemetry reading is associated with a device_id, sequence_number,
timestamp, and arbitrary sensor values.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class TelemetryRecord(BaseModel):
    """
    Standard stored telemetry entry in MongoDB.
    """
    event_id: str
    device_id: str
    device_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    telemetry_type: str = "general_telemetry"
    sequence_number: int = 1
    firmware_version: str = "1.0.0"
    correlation_id: Optional[str] = None
    values: Dict[str, Any] = Field(default_factory=dict)
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)


class TelemetryQueryFilter(BaseModel):
    """Filter parameters for querying historical telemetry."""
    device_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100
    skip: int = 0