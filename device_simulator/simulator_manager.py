"""
Simulator Manager — Device Simulator Fleet Runner

Manages the lifecycle of multiple virtual devices running in the same process.
Loads configured devices, creates corresponding VirtualDevice instances,
and manages async execution.
"""

import asyncio
from typing import Dict, List, Optional, Any
import structlog

from device_simulator.devices.base import VirtualDevice
from device_simulator.devices.sensors import (
    VirtualTemperatureSensor,
    VirtualMotionSensor,
    VirtualSmartActuator,
)
from app.models.device import DeviceType

logger = structlog.get_logger(__name__)


class SimulatorManager:
    """
    Manages a fleet of virtual simulated devices.
    """

    def __init__(self):
        self._devices: Dict[str, VirtualDevice] = {}
        self._is_running = False

    def register_device(self, device: VirtualDevice) -> None:
        """Register a device instance into the manager."""
        self._devices[device.device_id] = device
        logger.info("simulator_device_registered", device_id=device.device_id, type=device.device_type)

    def create_device_from_dict(
        self,
        config: Dict[str, Any],
        on_telemetry_emit: Optional[Any] = None,
        on_heartbeat_emit: Optional[Any] = None,
    ) -> VirtualDevice:
        """Factory creating the proper VirtualDevice subclass from configuration."""
        device_id = config["device_id"]
        device_name = config.get("device_name", device_id)
        device_type = config.get("device_type")
        hb = config.get("heartbeat_interval_seconds", 15)
        tel = config.get("telemetry_interval_seconds", 10)

        kwargs = {
            "device_id": device_id,
            "device_name": device_name,
            "heartbeat_interval": hb,
            "telemetry_interval": tel,
            "on_telemetry_emit": on_telemetry_emit,
            "on_heartbeat_emit": on_heartbeat_emit,
        }

        if device_type == DeviceType.TEMPERATURE_SENSOR.value or device_type == DeviceType.TEMPERATURE_SENSOR:
            device = VirtualTemperatureSensor(**kwargs)
        elif device_type == DeviceType.MOTION_SENSOR.value or device_type == DeviceType.MOTION_SENSOR:
            device = VirtualMotionSensor(**kwargs)
        elif device_type == DeviceType.SMART_ACTUATOR.value or device_type == DeviceType.SMART_ACTUATOR:
            device = VirtualSmartActuator(**kwargs)
        else:
            # Fallback to temperature sensor
            device = VirtualTemperatureSensor(**kwargs)

        self.register_device(device)
        return device

    async def start_all(self) -> None:
        """Start all registered devices."""
        self._is_running = True
        logger.info("simulator_starting_all", count=len(self._devices))
        for device in self._devices.values():
            await device.startup()

    async def stop_all(self) -> None:
        """Stop all registered devices."""
        self._is_running = False
        logger.info("simulator_stopping_all", count=len(self._devices))
        for device in self._devices.values():
            await device.shutdown()

    def get_device(self, device_id: str) -> Optional[VirtualDevice]:
        """Get device by ID."""
        return self._devices.get(device_id)

    @property
    def active_devices_count(self) -> int:
        return sum(1 for d in self._devices.values() if d.is_running)

    @property
    def total_devices_count(self) -> int:
        return len(self._devices)