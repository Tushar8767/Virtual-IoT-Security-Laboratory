"""
Telemetry Repository — MongoDB Persistence

Handles insert, retrieval, latest readings, and query filtering
for device telemetry.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import structlog
from app.core.database import get_database

logger = structlog.get_logger(__name__)
COLLECTION = "telemetry"


class TelemetryRepository:
    """Async repository for telemetry data in MongoDB."""

    def __init__(self, db=None):
        self.db = db if db is not None else get_database()
        self.collection = self.db[COLLECTION]

    async def insert(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new telemetry document."""
        if "ingested_at" not in record:
            record["ingested_at"] = datetime.now(timezone.utc)
        if isinstance(record.get("timestamp"), str):
            try:
                record["timestamp"] = datetime.fromisoformat(record["timestamp"])
            except Exception:
                record["timestamp"] = datetime.now(timezone.utc)

        await self.collection.insert_one(record)
        return record

    async def find_by_device(
        self,
        device_id: str,
        limit: int = 50,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Query historical telemetry for a device."""
        query: Dict[str, Any] = {"device_id": device_id}

        if start_time or end_time:
            query["timestamp"] = {}
            if start_time:
                query["timestamp"]["$gte"] = start_time
            if end_time:
                query["timestamp"]["$lte"] = end_time

        cursor = self.collection.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_latest_by_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent telemetry packet for a device."""
        docs = await self.find_by_device(device_id, limit=1)
        return docs[0] if docs else None

    async def get_latest_fleet_telemetry(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent telemetry stream across all devices."""
        cursor = self.collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def count_by_device(self, device_id: str) -> int:
        """Count total telemetry entries for a device."""
        return await self.collection.count_documents({"device_id": device_id})


def get_telemetry_repository() -> TelemetryRepository:
    return TelemetryRepository(get_database())