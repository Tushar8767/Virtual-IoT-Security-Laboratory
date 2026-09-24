"""
Telemetry Message Handler — Phase 0 Skeleton

Handles incoming MQTT messages for telemetry, heartbeat, and device events.
Full implementation in Phase 4 (Telemetry Pipeline).
"""

import json
import structlog

logger = structlog.get_logger(__name__)


async def handle_telemetry_message(device_id: str, payload: bytes) -> None:
    """
    Handle an incoming telemetry message from a device.
    Phase 0: Log and acknowledge only.
    Phase 4: Full validation, processing, persistence, and WebSocket broadcast.
    """
    try:
        data = json.loads(payload)
        logger.debug(
            "telemetry_received_stub",
            device_id=device_id,
            keys=list(data.keys()) if isinstance(data, dict) else None,
        )
    except json.JSONDecodeError as e:
        logger.warning(
            "telemetry_invalid_json",
            device_id=device_id,
            error=str(e),
        )


async def handle_heartbeat_message(device_id: str, payload: bytes) -> None:
    """
    Handle an incoming heartbeat message from a device.
    Phase 0: Log only.
    Phase 2+: Update device last_seen and status.
    """
    try:
        data = json.loads(payload)
        logger.debug(
            "heartbeat_received_stub",
            device_id=device_id,
            timestamp=data.get("timestamp"),
        )
    except json.JSONDecodeError as e:
        logger.warning(
            "heartbeat_invalid_json",
            device_id=device_id,
            error=str(e),
        )


async def handle_device_event_message(device_id: str, payload: bytes) -> None:
    """
    Handle an incoming device event message.
    Phase 0: Log only.
    Phase 7+: Route to security engine.
    """
    try:
        data = json.loads(payload)
        logger.debug(
            "device_event_received_stub",
            device_id=device_id,
            event_type=data.get("event_type"),
        )
    except json.JSONDecodeError as e:
        logger.warning(
            "device_event_invalid_json",
            device_id=device_id,
            error=str(e),
        )
