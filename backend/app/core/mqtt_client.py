"""
MQTT Client — Async connection management for the backend.

The backend connects to the MQTT broker to:
- Subscribe to device telemetry topics
- Subscribe to device heartbeat topics
- Subscribe to device event topics
- Publish commands to devices

Uses aiomqtt for async MQTT operations.
"""

import asyncio
import structlog
from typing import Optional, Callable, Any
from app.core.config import settings

logger = structlog.get_logger(__name__)

# Global MQTT client state
_mqtt_connected: bool = False
_mqtt_client: Optional[Any] = None
_mqtt_task: Optional[asyncio.Task] = None

# Topic prefix for all lab devices
LAB_TOPIC_PREFIX = "lab/devices"

# Wildcard subscriptions for the backend listener
SUBSCRIPTIONS = [
    f"{LAB_TOPIC_PREFIX}/+/telemetry",
    f"{LAB_TOPIC_PREFIX}/+/heartbeat",
    f"{LAB_TOPIC_PREFIX}/+/events",
]


async def connect_mqtt() -> None:
    """
    Initialize MQTT connection.
    Starts the background listener task.
    """
    global _mqtt_connected, _mqtt_task

    try:
        import aiomqtt

        # Test connectivity synchronously first
        _mqtt_connected = await _test_mqtt_connection()

        if _mqtt_connected:
            # Start the background MQTT listener
            _mqtt_task = asyncio.create_task(
                _mqtt_listener_loop(),
                name="mqtt-listener",
            )
            logger.info(
                "mqtt_listener_started",
                host=settings.MQTT_BROKER_HOST,
                port=settings.MQTT_BROKER_PORT,
            )
        else:
            logger.warning(
                "mqtt_connection_failed_running_degraded",
                host=settings.MQTT_BROKER_HOST,
                port=settings.MQTT_BROKER_PORT,
            )

    except ImportError:
        logger.error("aiomqtt_not_installed")
        _mqtt_connected = False


async def _test_mqtt_connection() -> bool:
    """
    Test MQTT broker reachability with a short timeout.
    Returns True if broker is reachable.
    """
    try:
        import aiomqtt

        async with aiomqtt.Client(
            hostname=settings.MQTT_BROKER_HOST,
            port=settings.MQTT_BROKER_PORT,
            identifier=f"{settings.MQTT_CLIENT_ID_PREFIX}-probe",
            timeout=5.0,
        ):
            return True

    except Exception as e:
        logger.warning("mqtt_probe_failed", error=str(e))
        return False


async def _mqtt_listener_loop() -> None:
    """
    Background MQTT listener.
    Subscribes to device topics and dispatches messages to handlers.
    Reconnects automatically on disconnection.
    """
    import aiomqtt

    reconnect_interval = 5

    while True:
        try:
            async with aiomqtt.Client(
                hostname=settings.MQTT_BROKER_HOST,
                port=settings.MQTT_BROKER_PORT,
                identifier=f"{settings.MQTT_CLIENT_ID_PREFIX}-listener",
                timeout=10.0,
            ) as client:
                global _mqtt_connected
                _mqtt_connected = True

                # Subscribe to all device topics
                for topic in SUBSCRIPTIONS:
                    await client.subscribe(topic)
                    logger.info("mqtt_subscribed", topic=topic)

                # Process incoming messages
                async for message in client.messages:
                    await _dispatch_message(
                        topic=str(message.topic),
                        payload=message.payload,
                    )

        except Exception as e:
            _mqtt_connected = False
            logger.warning(
                "mqtt_listener_disconnected",
                error=str(e),
                retry_in=reconnect_interval,
            )
            await asyncio.sleep(reconnect_interval)


async def _dispatch_message(topic: str, payload: bytes) -> None:
    """
    Dispatch an incoming MQTT message to the appropriate handler.
    """
    try:
        parts = topic.split("/")
        # Expected: lab/devices/{device_id}/{message_type}
        if len(parts) != 4:
            logger.warning("mqtt_invalid_topic_format", topic=topic)
            return

        _, _, device_id, message_type = parts

        logger.debug(
            "mqtt_message_received",
            topic=topic,
            device_id=device_id,
            message_type=message_type,
            payload_size=len(payload),
        )

        # Import handlers lazily to avoid circular imports
        if message_type == "telemetry":
            from app.telemetry.handler import handle_telemetry_message
            await handle_telemetry_message(device_id, payload)

        elif message_type == "heartbeat":
            from app.telemetry.handler import handle_heartbeat_message
            await handle_heartbeat_message(device_id, payload)

        elif message_type == "events":
            from app.telemetry.handler import handle_device_event_message
            await handle_device_event_message(device_id, payload)

        else:
            logger.warning(
                "mqtt_unknown_message_type",
                topic=topic,
                message_type=message_type,
            )

    except Exception as e:
        logger.error("mqtt_dispatch_error", topic=topic, error=str(e))


async def disconnect_mqtt() -> None:
    """
    Disconnect MQTT and cancel the listener task.
    """
    global _mqtt_connected, _mqtt_task

    if _mqtt_task and not _mqtt_task.done():
        _mqtt_task.cancel()
        try:
            await _mqtt_task
        except asyncio.CancelledError:
            pass

    _mqtt_connected = False
    logger.info("mqtt_disconnected")


def get_mqtt_status() -> dict:
    """
    Return current MQTT connection status.
    Used by the health endpoint.
    """
    return {
        "connected": _mqtt_connected,
        "broker_host": settings.MQTT_BROKER_HOST,
        "broker_port": settings.MQTT_BROKER_PORT,
        "listener_active": _mqtt_task is not None and not _mqtt_task.done(),
    }


async def publish_command(device_id: str, payload: dict) -> bool:
    """
    Publish a command message to a specific device.
    Returns True if published successfully.
    """
    import json
    import aiomqtt

    topic = f"{LAB_TOPIC_PREFIX}/{device_id}/commands"

    try:
        async with aiomqtt.Client(
            hostname=settings.MQTT_BROKER_HOST,
            port=settings.MQTT_BROKER_PORT,
            identifier=f"{settings.MQTT_CLIENT_ID_PREFIX}-publisher",
            timeout=5.0,
        ) as client:
            await client.publish(topic, json.dumps(payload).encode())
            logger.info("mqtt_command_published", device_id=device_id, topic=topic)
            return True

    except Exception as e:
        logger.error("mqtt_publish_failed", device_id=device_id, error=str(e))
        return False

