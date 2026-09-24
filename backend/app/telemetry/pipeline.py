"""
Telemetry Processing Pipeline

Consumes validated messages, persists telemetry, updates device status,
and broadcasts events to WebSocket clients.
"""

from typing import Dict, Any, Tuple
import structlog
from app.repositories.telemetry_repository import TelemetryRepository
from app.repositories.device_repository import DeviceRepository
from app.models.device import DeviceStatus
from app.api.websocket import broadcast_event

logger = structlog.get_logger(__name__)


class TelemetryPipeline:
    """
    Ingestion pipeline processing incoming sensor feeds.
    """

    def __init__(
        self,
        telemetry_repo: TelemetryRepository,
        device_repo: DeviceRepository,
    ):
        self.telemetry_repo = telemetry_repo
        self.device_repo = device_repo

    async def process_telemetry(self, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Process, persist, and broadcast an incoming telemetry message.
        """
        device_id = payload.get("device_id")
        if not device_id:
            return False, "MISSING_DEVICE_ID"

        # 1. Persist record
        try:
            await self.telemetry_repo.insert(payload)
        except Exception as e:
            logger.error("telemetry_insert_failed", device_id=device_id, error=str(e))
            return False, f"PERSISTENCE_ERROR: {str(e)}"

        # 2. Update device last seen & set ONLINE if PROVISIONED
        try:
            await self.device_repo.update_last_seen(device_id)
            device = await self.device_repo.find_by_id(device_id)
            if device and device.get("status") == DeviceStatus.PROVISIONED.value:
                await self.device_repo.update_status(device_id, DeviceStatus.ONLINE.value)
                await broadcast_event("device_status_changed", {
                    "device_id": device_id,
                    "status": DeviceStatus.ONLINE.value,
                    "event": "device_came_online",
                })
        except Exception as e:
            logger.warning("device_status_update_failed", device_id=device_id, error=str(e))

        # 3. Broadcast to real-time WebSocket dashboard
        try:
            # Strip internal ID if present
            broadcast_payload = dict(payload)
            broadcast_payload.pop("_id", None)
            await broadcast_event("telemetry_received", broadcast_payload)
        except Exception as e:
            logger.debug("ws_broadcast_failed", error=str(e))

        logger.info("telemetry_processed", device_id=device_id, sequence=payload.get("sequence_number"))
        return True, "SUCCESS"