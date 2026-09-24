"""
WebSocket Manager — Real-time event delivery

Manages WebSocket connections and broadcasts structured events
to all connected dashboard clients.

Full event integration in Phase 4+.
Phase 0 provides the connection infrastructure.
"""

import json
import asyncio
import structlog
from typing import Dict, Set
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """
    Manages active WebSocket connections.
    Supports broadcast, targeted send, and graceful disconnect.
    """

    def __init__(self):
        # Set of active connections
        self._connections: Set[WebSocket] = set()
        # Bounded event history (last N events for new connections)
        self._event_history: list = []
        self._max_history: int = 100

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._connections.add(websocket)
        logger.info(
            "websocket_client_connected",
            total_connections=len(self._connections),
            client=websocket.client,
        )

        # Send recent event history to new client
        if self._event_history:
            try:
                await websocket.send_json({
                    "event_type": "connection_established",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "message": "Connected to Virtual IoT Security Lab real-time feed",
                    "recent_events_count": len(self._event_history),
                })
            except Exception:
                pass

    def disconnect(self, websocket: WebSocket) -> None:
        """Unregister a disconnected WebSocket."""
        self._connections.discard(websocket)
        logger.info(
            "websocket_client_disconnected",
            total_connections=len(self._connections),
        )

    async def broadcast(self, event: dict) -> None:
        """
        Broadcast an event to all connected clients.
        Disconnected clients are removed automatically.
        """
        if not self._connections:
            return

        # Add to event history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

        # Broadcast to all connected clients
        disconnected = set()
        message = json.dumps(event)

        for connection in self._connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self._connections.discard(connection)

        if disconnected:
            logger.info(
                "websocket_cleaned_disconnected",
                removed=len(disconnected),
                remaining=len(self._connections),
            )

    @property
    def connection_count(self) -> int:
        return len(self._connections)


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time dashboard events.

    Clients connect here to receive:
    - device_status_changed
    - telemetry_received
    - security_event_created
    - alert_created
    - scenario_started
    - scenario_completed
    - heartbeat_ping (keepalive)
    """
    await manager.connect(websocket)

    try:
        while True:
            try:
                # Keep connection alive with a ping/pong heartbeat
                # Client messages can send keepalive pings
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0,
                )

                # Handle client ping
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                except json.JSONDecodeError:
                    pass

            except asyncio.TimeoutError:
                # Send server-side heartbeat ping
                try:
                    await websocket.send_json({
                        "event_type": "heartbeat_ping",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "active_connections": manager.connection_count,
                    })
                except Exception:
                    break

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning("websocket_error", error=str(e))
        manager.disconnect(websocket)


async def broadcast_event(event_type: str, data: dict) -> None:
    """
    Helper to broadcast a typed event to all connected clients.
    Called by backend services when events occur.
    """
    event = {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **data,
    }
    await manager.broadcast(event)

