"""
Database Connection Management

Manages the async MongoDB connection using motor.
Provides dependency injection helpers for FastAPI routes.
"""

import structlog
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = structlog.get_logger(__name__)

# Global client and database references
_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongodb() -> None:
    """
    Initialize MongoDB connection.
    Called during application startup.
    """
    global _client, _database

    _client = AsyncIOMotorClient(
        settings.MONGODB_URI,
        maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
        serverSelectionTimeoutMS=5000,
    )

    # Force connection by pinging the server
    await _client.admin.command("ping")

    _database = _client[settings.MONGODB_DATABASE]

    # Create indexes for all collections
    await _create_indexes()

    logger.info(
        "mongodb_connected",
        database=settings.MONGODB_DATABASE,
        uri=settings.MONGODB_URI,
    )


async def close_mongodb_connection() -> None:
    """
    Close MongoDB connection.
    Called during application shutdown.
    """
    global _client, _database

    if _client is not None:
        _client.close()
        _client = None
        _database = None
        logger.info("mongodb_disconnected")


def get_database() -> AsyncIOMotorDatabase:
    """
    Get the database instance.
    Raises RuntimeError if not connected.
    """
    if _database is None:
        raise RuntimeError(
            "Database not connected. Ensure connect_to_mongodb() was called."
        )
    return _database


async def get_database_status() -> dict:
    """
    Get current database connection status.
    Used by the health endpoint.
    """
    try:
        if _client is None:
            return {"connected": False, "error": "Client not initialized"}

        result = await _client.admin.command("ping")
        return {
            "connected": True,
            "database": settings.MONGODB_DATABASE,
            "ping": result.get("ok") == 1.0,
        }
    except Exception as e:
        logger.warning("database_health_check_failed", error=str(e))
        return {"connected": False, "error": str(e)}


async def _create_indexes() -> None:
    """
    Create MongoDB indexes for all collections.
    Indexes are created idempotently (safe to call multiple times).
    """
    if _database is None:
        return

    from pymongo import ASCENDING, DESCENDING

    # devices
    await _database.devices.create_index(
        [("device_id", ASCENDING)], unique=True, name="idx_device_id"
    )
    await _database.devices.create_index(
        [("status", ASCENDING)], name="idx_device_status"
    )
    await _database.devices.create_index(
        [("device_type", ASCENDING)], name="idx_device_type"
    )

    # telemetry
    await _database.telemetry.create_index(
        [("device_id", ASCENDING), ("timestamp", DESCENDING)],
        name="idx_telemetry_device_time",
    )
    await _database.telemetry.create_index(
        [("timestamp", DESCENDING)], name="idx_telemetry_timestamp"
    )

    # security_events
    await _database.security_events.create_index(
        [("event_id", ASCENDING)], unique=True, name="idx_security_event_id"
    )
    await _database.security_events.create_index(
        [("device_id", ASCENDING), ("timestamp", DESCENDING)],
        name="idx_security_events_device_time",
    )
    await _database.security_events.create_index(
        [("severity", ASCENDING)], name="idx_security_events_severity"
    )
    await _database.security_events.create_index(
        [("correlation_id", ASCENDING)], name="idx_security_events_correlation"
    )
    await _database.security_events.create_index(
        [("timestamp", DESCENDING)], name="idx_security_events_timestamp"
    )

    # alerts
    await _database.alerts.create_index(
        [("alert_id", ASCENDING)], unique=True, name="idx_alert_id"
    )
    await _database.alerts.create_index(
        [("status", ASCENDING)], name="idx_alert_status"
    )
    await _database.alerts.create_index(
        [("severity", ASCENDING)], name="idx_alert_severity"
    )

    # audit_logs
    await _database.audit_logs.create_index(
        [("timestamp", DESCENDING)], name="idx_audit_timestamp"
    )
    await _database.audit_logs.create_index(
        [("correlation_id", ASCENDING)], name="idx_audit_correlation"
    )
    await _database.audit_logs.create_index(
        [("actor", ASCENDING)], name="idx_audit_actor"
    )

    # scenarios
    await _database.scenarios.create_index(
        [("scenario_id", ASCENDING)], unique=True, name="idx_scenario_id"
    )

    logger.info("database_indexes_created")

