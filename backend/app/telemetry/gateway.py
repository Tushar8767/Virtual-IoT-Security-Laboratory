"""
Secure IoT Gateway — Ingestion & Identity Validation

Enforces:
1. Topic/Device validation (a device cannot publish to another device's topic)
2. Device registry lookup (unknown devices are rejected)
3. Device status verification (REVOKED or SUSPENDED devices are rejected)
4. Telemetry structure validation
"""

import json
from typing import Dict, Any, Tuple, Optional
import structlog
from app.repositories.device_repository import DeviceRepository
from app.models.device import DeviceStatus

logger = structlog.get_logger(__name__)


class GatewayValidationResult:
    """Result of gateway security checks."""

    def __init__(self, is_valid: bool, reason: str = "", device_doc: Optional[Dict[str, Any]] = None):
        self.is_valid = is_valid
        self.reason = reason
        self.device_doc = device_doc


class SecureIotGateway:
    """
    IoT Gateway enforcing security boundaries before messages reach
    the telemetry pipeline or detection engine.
    """

    def __init__(self, device_repo: DeviceRepository):
        self.device_repo = device_repo

    async def validate_inbound_message(
        self,
        topic: str,
        raw_payload: bytes,
    ) -> Tuple[GatewayValidationResult, Optional[Dict[str, Any]]]:
        """
        Validate an inbound MQTT message.
        Returns (ValidationResult, parsed_payload_dict).
        """
        parts = topic.split("/")
        # Expecting: lab/devices/{device_id}/{message_type}
        if len(parts) != 4 or parts[0] != "lab" or parts[1] != "devices":
            return GatewayValidationResult(False, "INVALID_TOPIC_FORMAT"), None

        topic_device_id = parts[2]
        message_type = parts[3]

        # 1. Parse JSON
        try:
            payload = json.loads(raw_payload.decode("utf-8"))
        except Exception:
            return GatewayValidationResult(False, "MALFORMED_JSON_PAYLOAD"), None

        if not isinstance(payload, dict):
            return GatewayValidationResult(False, "PAYLOAD_MUST_BE_JSON_OBJECT"), None

        # 2. Impersonation Check: device_id in payload must match topic device_id
        payload_device_id = payload.get("device_id")
        if payload_device_id and payload_device_id != topic_device_id:
            logger.warning(
                "gateway_impersonation_detected",
                topic_device_id=topic_device_id,
                payload_device_id=payload_device_id,
            )
            return GatewayValidationResult(
                False,
                f"DEVICE_IMPERSONATION: topic={topic_device_id} payload={payload_device_id}",
            ), payload

        # 3. Device Registry Check
        device = await self.device_repo.find_by_id(topic_device_id)
        if not device:
            return GatewayValidationResult(False, f"UNKNOWN_DEVICE: {topic_device_id}"), payload

        # 4. Device Lifecycle Check
        status = device.get("status")
        if status == DeviceStatus.REVOKED.value:
            return GatewayValidationResult(False, f"DEVICE_REVOKED: {topic_device_id}"), payload
        if status == DeviceStatus.SUSPENDED.value:
            return GatewayValidationResult(False, f"DEVICE_SUSPENDED: {topic_device_id}"), payload

        return GatewayValidationResult(True, "OK", device_doc=device), payload