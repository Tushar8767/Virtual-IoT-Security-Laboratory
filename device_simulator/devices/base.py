"""
Virtual Device Base Class — Device Simulator

Provides the base asynchronous implementation for all simulated IoT devices.
Supports:
- Async lifecycle (startup, shutdown)
- Configurable telemetry and heartbeat intervals
- Sequence numbers and correlation tracking
- Normal and abnormal simulation modes
- Standard JSON payload formatting matching project specification
"""

import abc
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Callable
import structlog

logger = structlog.get_logger(__name__)


class VirtualDevice(abc.ABC):
    """
    Abstract base class for simulated IoT devices.
    Runs asynchronously without requiring physical hardware.
    """

    def __init__(
        self,
        device_id: str,
        device_name: str,
        device_type: str,
        api_key: Optional[str] = None,
        heartbeat_interval: int = 15,
        telemetry_interval: int = 10,
        firmware_version: str = "1.0.0",
        on_telemetry_emit: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_heartbeat_emit: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ):
        self.device_id = device_id
        self.device_name = device_name
        self.device_type = device_type
        self.api_key = api_key
        self.heartbeat_interval = heartbeat_interval
        self.telemetry_interval = telemetry_interval
        self.firmware_version = firmware_version

        # Emission callbacks (can route to MQTT, HTTP, or internal queue)
        self.on_telemetry_emit = on_telemetry_emit
        self.on_heartbeat_emit = on_heartbeat_emit

        # State tracking
        self.is_running = False
        self._sequence_number = 0
        self._telemetry_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

        # Behavior modes: 'normal', 'stress', 'abnormal'
        self.mode = "normal"

    @abc.abstractmethod
    def generate_sensor_values(self) -> Dict[str, Any]:
        """
        Generate device-specific sensor values.
        Must be implemented by subclasses.
        """
        pass

    def now_iso(self) -> str:
        """UTC timestamp formatted as ISO-8601 string."""
        return datetime.now(timezone.utc).isoformat()

    def next_sequence(self) -> int:
        """Atomic increment sequence number."""
        self._sequence_number += 1
        return self._sequence_number

    def build_telemetry_payload(self) -> Dict[str, Any]:
        """Format standard telemetry payload matching project schema."""
        values = self.generate_sensor_values()
        return {
            "event_id": f"tel-{uuid.uuid4().hex[:12]}",
            "device_id": self.device_id,
            "device_type": self.device_type,
            "timestamp": self.now_iso(),
            "telemetry_type": f"{self.device_type}_telemetry",
            "sequence_number": self.next_sequence(),
            "firmware_version": self.firmware_version,
            "correlation_id": str(uuid.uuid4()),
            "values": values,
        }

    def build_heartbeat_payload(self) -> Dict[str, Any]:
        """Format standard heartbeat payload."""
        return {
            "event_id": f"hb-{uuid.uuid4().hex[:12]}",
            "device_id": self.device_id,
            "timestamp": self.now_iso(),
            "status": "ONLINE",
            "sequence_number": self.next_sequence(),
            "firmware_version": self.firmware_version,
        }

    async def startup(self) -> None:
        """Start device telemetry and heartbeat loops."""
        if self.is_running:
            return

        self.is_running = True
        logger.info("virtual_device_started", device_id=self.device_id, type=self.device_type)

        # Launch periodic loops
        self._telemetry_task = asyncio.create_task(self._telemetry_loop(), name=f"{self.device_id}-telemetry")
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop(), name=f"{self.device_id}-heartbeat")

    async def shutdown(self) -> None:
        """Stop device loops cleanly."""
        self.is_running = False

        for task in (self._telemetry_task, self._heartbeat_task):
            if task and not task.done():
                try:
                    task.cancel()
                    # Only await if attached to the current active event loop
                    if task.get_loop() == asyncio.get_running_loop():
                        await task
                except (asyncio.CancelledError, RuntimeError):
                    pass

        self._telemetry_task = None
        self._heartbeat_task = None
        logger.info("virtual_device_stopped", device_id=self.device_id)

    async def _telemetry_loop(self) -> None:
        """Loop emitting periodic telemetry."""
        while self.is_running:
            try:
                payload = self.build_telemetry_payload()
                if self.on_telemetry_emit:
                    if asyncio.iscoroutinefunction(self.on_telemetry_emit):
                        await self.on_telemetry_emit(payload)
                    else:
                        self.on_telemetry_emit(payload)
            except Exception as e:
                logger.error("virtual_device_telemetry_error", device_id=self.device_id, error=str(e))

            interval = self.telemetry_interval if self.mode != "stress" else max(1, self.telemetry_interval // 5)
            await asyncio.sleep(interval)

    async def _heartbeat_loop(self) -> None:
        """Loop emitting periodic heartbeats."""
        while self.is_running:
            try:
                payload = self.build_heartbeat_payload()
                if self.on_heartbeat_emit:
                    if asyncio.iscoroutinefunction(self.on_heartbeat_emit):
                        await self.on_heartbeat_emit(payload)
                    else:
                        self.on_heartbeat_emit(payload)
            except Exception as e:
                logger.error("virtual_device_heartbeat_error", device_id=self.device_id, error=str(e))

            await asyncio.sleep(self.heartbeat_interval)