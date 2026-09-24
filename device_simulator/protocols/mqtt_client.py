"""
Virtual Device MQTT Client — Protocol Layer

Enables virtual devices to publish telemetry and heartbeat payloads
over MQTT to the Secure IoT Gateway.
"""

import json
import asyncio
from typing import Dict, Any, Optional
import structlog
import aiomqtt

logger = structlog.get_logger(__name__)


class DeviceMqttPublisher:
    """
    Asynchronous MQTT publisher for simulated devices.
    """

    def __init__(
        self,
        device_id: str,
        api_key: Optional[str] = None,
        broker_host: str = "localhost",
        broker_port: int = 1883,
    ):
        self.device_id = device_id
        self.api_key = api_key
        self.broker_host = broker_host
        self.broker_port = broker_port

        self.telemetry_topic = f"lab/devices/{self.device_id}/telemetry"
        self.heartbeat_topic = f"lab/devices/{self.device_id}/heartbeat"

    async def publish_telemetry(self, payload: Dict[str, Any]) -> bool:
        """Publish a telemetry payload to the device's telemetry topic."""
        return await self._publish(self.telemetry_topic, payload)

    async def publish_heartbeat(self, payload: Dict[str, Any]) -> bool:
        """Publish a heartbeat payload to the device's heartbeat topic."""
        return await self._publish(self.heartbeat_topic, payload)

    async def _publish(self, topic: str, data: Dict[str, Any]) -> bool:
        try:
            # Include API key in payload header for gateway verification
            if self.api_key and "api_key" not in data:
                data["api_key"] = self.api_key

            message = json.dumps(data)

            async with aiomqtt.Client(
                hostname=self.broker_host,
                port=self.broker_port,
                identifier=f"client-{self.device_id}",
                timeout=5.0,
            ) as client:
                await client.publish(topic, message.encode("utf-8"), qos=1)

            logger.debug("mqtt_published", topic=topic, device_id=self.device_id)
            return True

        except Exception as e:
            logger.warning("mqtt_publish_failed", topic=topic, error=str(e))
            return False