"""
Database Connection Management

Manages the async MongoDB connection using motor.
Provides an automatic in-memory development fallback when MongoDB
is not installed or running locally.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import structlog
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = structlog.get_logger(__name__)

# Global client and database references
_client: Optional[AsyncIOMotorClient] = None
_database: Optional[Any] = None
_is_in_memory: bool = False


# ============================================================
# In-Memory Development Database Fallback
# ============================================================

class _InMemoryCursor:
    """Async cursor simulating MongoDB cursor for local dev."""

    def __init__(self, docs: List[Dict[str, Any]]):
        self._docs = list(docs)

    def sort(self, key_or_list: Any, direction: Optional[int] = None) -> "_InMemoryCursor":
        # Basic sorting support
        if isinstance(key_or_list, str):
            reverse = direction == -1
            self._docs.sort(key=lambda d: d.get(key_or_list, 0) or 0, reverse=reverse)
        return self

    def skip(self, count: int) -> "_InMemoryCursor":
        self._docs = self._docs[count:]
        return self

    def limit(self, count: int) -> "_InMemoryCursor":
        self._docs = self._docs[:count]
        return self

    async def to_list(self, length: Optional[int] = None) -> List[Dict[str, Any]]:
        if length is not None:
            return self._docs[:length]
        return list(self._docs)


class _InMemoryCollection:
    """In-memory collection simulating a Motor collection."""

    def __init__(self, name: str):
        self.name = name
        self._store: Dict[str, Dict[str, Any]] = {}

    async def create_index(self, *args, **kwargs):
        pass

    async def insert_one(self, doc: Dict[str, Any]) -> Any:
        # Clone doc to avoid outside mutation
        stored = dict(doc)
        key = str(stored.get("device_id") or stored.get("audit_id") or stored.get("event_id") or len(self._store))
        self._store[key] = stored

        class InsertResult:
            inserted_id = key

        return InsertResult()

    async def find_one(self, query: Dict[str, Any], projection: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        for item in self._store.values():
            match = True
            for k, v in query.items():
                if item.get(k) != v:
                    match = False
                    break
            if match:
                res = dict(item)
                if projection and projection.get("_id") == 0:
                    res.pop("_id", None)
                return res
        return None

    def find(self, query: Optional[Dict[str, Any]] = None, projection: Optional[Dict[str, Any]] = None) -> _InMemoryCursor:
        query = query or {}
        matches = []
        for item in self._store.values():
            match = True
            for k, v in query.items():
                if item.get(k) != v:
                    match = False
                    break
            if match:
                res = dict(item)
                if projection and projection.get("_id") == 0:
                    res.pop("_id", None)
                matches.append(res)
        return _InMemoryCursor(matches)

    async def count_documents(self, query: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> int:
        cursor = self.find(query)
        docs = await cursor.to_list(limit)
        return len(docs)

    async def find_one_and_update(
        self,
        query: Dict[str, Any],
        update: Dict[str, Any],
        return_document: bool = True,
        projection: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        doc = await self.find_one(query)
        if not doc:
            return None

        # Apply $set
        if "$set" in update:
            for k, v in update["$set"].items():
                doc[k] = v

        # Apply $inc
        if "$inc" in update:
            for k, v in update["$inc"].items():
                doc[k] = doc.get(k, 0) + v

        key = str(doc.get("device_id") or doc.get("audit_id") or doc.get("event_id") or len(self._store))
        self._store[key] = doc

        res = dict(doc)
        if projection and projection.get("_id") == 0:
            res.pop("_id", None)
        return res

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any]) -> Any:
        return await self.find_one_and_update(query, update)

    async def aggregate(self, pipeline: List[Dict[str, Any]]) -> _InMemoryCursor:
        # Simple status aggregator
        counts: Dict[str, int] = {}
        for item in self._store.values():
            st = item.get("status")
            if st:
                counts[st] = counts.get(st, 0) + 1
        results = [{"_id": st, "count": c} for st, c in counts.items()]
        return _InMemoryCursor(results)

    async def drop(self):
        self._store.clear()


class _InMemoryDatabase:
    """In-memory database holding simulated collections."""

    def __init__(self, name: str):
        self.name = name
        self._collections: Dict[str, _InMemoryCollection] = {}

    def __getitem__(self, name: str) -> _InMemoryCollection:
        if name not in self._collections:
            self._collections[name] = _InMemoryCollection(name)
        return self._collections[name]

    def __getattr__(self, name: str) -> _InMemoryCollection:
        return self[name]


# ============================================================
# Connection Logic
# ============================================================

async def connect_to_mongodb() -> None:
    """
    Initialize database connection.
    Attempts MongoDB first; falls back to in-memory mode if unreachable.
    """
    global _client, _database, _is_in_memory

    try:
        client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
            serverSelectionTimeoutMS=2000,
        )
        # Probe connection
        await client.admin.command("ping")
        _client = client
        _database = _client[settings.MONGODB_DATABASE]
        _is_in_memory = False
        await _create_indexes()
        logger.info(
            "mongodb_connected",
            database=settings.MONGODB_DATABASE,
            uri=settings.MONGODB_URI,
        )
    except Exception as e:
        logger.warning(
            "mongodb_connection_failed_using_in_memory_fallback",
            uri=settings.MONGODB_URI,
            reason=str(e),
        )
        _client = None
        _database = _InMemoryDatabase(settings.MONGODB_DATABASE)
        _is_in_memory = True
        logger.info(
            "in_memory_database_initialized",
            database=settings.MONGODB_DATABASE,
            note="Running in development fallback mode (no external MongoDB required)",
        )


async def close_mongodb_connection() -> None:
    """Close database connection."""
    global _client, _database, _is_in_memory

    if _client is not None:
        _client.close()
        _client = None
        logger.info("mongodb_disconnected")
    _database = None
    _is_in_memory = False


def get_database() -> Any:
    """Get the active database instance (MongoDB or in-memory fallback)."""
    if _database is None:
        raise RuntimeError("Database not connected. Ensure connect_to_mongodb() was called.")
    return _database


async def get_database_status() -> dict:
    """Get current database connection status for health endpoint."""
    if _is_in_memory:
        return {
            "connected": True,
            "mode": "in_memory_dev_fallback",
            "database": settings.MONGODB_DATABASE,
            "ping": True,
            "note": "Running local in-memory persistence fallback",
        }
    try:
        if _client is None:
            return {"connected": False, "error": "Client not initialized"}
        result = await _client.admin.command("ping")
        return {
            "connected": True,
            "mode": "mongodb",
            "database": settings.MONGODB_DATABASE,
            "ping": result.get("ok") == 1.0,
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}


async def _create_indexes() -> None:
    """Create MongoDB indexes."""
    if _database is None or _is_in_memory:
        return

    from pymongo import ASCENDING, DESCENDING

    await _database.devices.create_index([("device_id", ASCENDING)], unique=True, name="idx_device_id")
    await _database.devices.create_index([("status", ASCENDING)], name="idx_device_status")
    await _database.devices.create_index([("device_type", ASCENDING)], name="idx_device_type")
    await _database.telemetry.create_index([("device_id", ASCENDING), ("timestamp", DESCENDING)], name="idx_telemetry_device_time")
    await _database.telemetry.create_index([("timestamp", DESCENDING)], name="idx_telemetry_timestamp")
    await _database.security_events.create_index([("event_id", ASCENDING)], unique=True, name="idx_security_event_id")
    await _database.security_events.create_index([("device_id", ASCENDING), ("timestamp", DESCENDING)], name="idx_security_events_device_time")
    await _database.security_events.create_index([("severity", ASCENDING)], name="idx_security_events_severity")
    await _database.security_events.create_index([("correlation_id", ASCENDING)], name="idx_security_events_correlation")
    await _database.alerts.create_index([("alert_id", ASCENDING)], unique=True, name="idx_alert_id")
    await _database.alerts.create_index([("status", ASCENDING)], name="idx_alert_status")
    await _database.audit_logs.create_index([("timestamp", DESCENDING)], name="idx_audit_timestamp")
    await _database.scenarios.create_index([("scenario_id", ASCENDING)], unique=True, name="idx_scenario_id")

    logger.info("database_indexes_created")