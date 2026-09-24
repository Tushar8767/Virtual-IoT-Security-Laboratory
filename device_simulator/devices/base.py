"""
Virtual Device Base Class — Phase 0 Skeleton

Defines the interface all simulated devices must implement.
Full implementation in Phase 2.
"""

import abc
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional


class VirtualDevice(abc.ABC):
    """
    Abstract base class for all virtual IoT devices.

    Every simulated device must implement:
    - startup(): Initialize device state
    - shutdown(): Clean up and stop
    - generate_telemetry(): Produce telemetry payload
    - send_heartbeat(): Send a heartbeat message

    Devices operate as independent async tasks.
    They do NOT require physical hardware.
    """

    def __init__(
        self,
        device_id: str,
        device_name: str,
        device_type: str,
        mqtt_host: str = "localhost",
        mqtt_port: int = 1883,
        heartbeat_interval: int = 15,
        telemetry_interval: int = 10,
    ):
        self.device_id = device_id
        self.device_name = device_name
        self.device_type = device_type
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.heartbeat_interval = heartbeat_interval
        self.telemetry_interval = telemetry_interval

        self.firmware_version = "1.0.0"
        self.is_running = False
        self._sequence_number = 0

        # MQTT topic prefix
        self.topic_prefix = f"lab/devices/{self.device_id}"

    @abc.abstractmethod
    async def generate_telemetry(self) -> dict:
        """
        Generate a telemetry payload.
        Must return a dict with device-appropriate sensor readings.
        """
        ...

    async def startup(self) -> None:
        """Initialize the device and start background tasks."""
        self.is_running = True

    async def shutdown(self) -> None:
        """Stop the device and clean up."""
        self.is_running = False

    async def send_heartbeat(self) -> None:
        """Send a heartbeat message via MQTT. Stub in Phase 0."""
        pass

    def next_sequence(self) -> int:
        """Get and increment the sequence number."""
        self._sequence_number += 1
        return self._sequence_number

    def now_iso(self) -> str:
        """Return current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.device_id} type={self.device_type}>"

