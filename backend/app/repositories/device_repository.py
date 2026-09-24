"""
Device Repository — MongoDB persistence layer

Handles all database operations for the Device collection.
No business logic here — that belongs in the service layer.

Collection: devices
"""

import structlog
from typing import Optional, List
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database

logger = structlog.get_logger(__name__)

COLLECTION = "devices"


class DeviceRepository:
    """
    Async MongoDB repository for Device documents.
    All methods return raw dicts from MongoDB (not domain objects).
    The service layer is responsible for mapping to domain models.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db[COLLECTION]

    # ----------------------------------------------------------
    # Read
    # ----------------------------------------------------------

    async def find_by_id(self, device_id: str) -> Optional[dict]:
        """Find a device by its device_id. Returns None if not found."""
        doc = await self.collection.find_one(
            {"device_id": device_id},
            {"_id": 0},  # exclude MongoDB _id
        )
        return doc

    async def find_all(
        self,
        status: Optional[str] = None,
        device_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[List[dict], int]:
        """
        List devices with optional filters and pagination.
        Returns (documents, total_count).
        """
        query: dict = {}
        if status:
            query["status"] = status
        if device_type:
            query["device_type"] = device_type

        total = await self.collection.count_documents(query)

        skip = (page - 1) * page_size
        cursor = (
            self.collection.find(query, {"_id": 0})
            .sort("created_at", -1)
            .skip(skip)
            .limit(page_size)
        )
        documents = await cursor.to_list(length=page_size)
        return documents, total

    async def exists(self, device_id: str) -> bool:
        """Return True if a device with this ID exists."""
        count = await self.collection.count_documents(
            {"device_id": device_id}, limit=1
        )
        return count > 0

    async def get_status_summary(self) -> dict:
        """Return counts of devices by status."""
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        results = await self.collection.aggregate(pipeline).to_list(length=None)
        summary = {r["_id"]: r["count"] for r in results}
        total = sum(summary.values())
        return {
            "total": total,
            "registered": summary.get("REGISTERED", 0),
            "provisioned": summary.get("PROVISIONED", 0),
            "online": summary.get("ONLINE", 0),
            "offline": summary.get("OFFLINE", 0),
            "suspended": summary.get("SUSPENDED", 0),
            "revoked": summary.get("REVOKED", 0),
        }

    # ----------------------------------------------------------
    # Write
    # ----------------------------------------------------------

    async def insert(self, document: dict) -> dict:
        """Insert a new device document. Returns the inserted document."""
        await self.collection.insert_one(document)
        # Re-fetch without _id to return clean document
        return await self.find_by_id(document["device_id"])

    async def update_fields(self, device_id: str, fields: dict) -> Optional[dict]:
        """
        Update specific fields on a device.
        Always sets updated_at to now.
        Returns the updated document, or None if not found.
        """
        fields["updated_at"] = datetime.now(timezone.utc)

        result = await self.collection.find_one_and_update(
            {"device_id": device_id},
            {"$set": fields},
            return_document=True,  # Return the updated document
            projection={"_id": 0},
        )
        return result

    async def update_status(self, device_id: str, new_status: str) -> Optional[dict]:
        """Update only the device status and updated_at timestamp."""
        return await self.update_fields(device_id, {"status": new_status})

    async def update_last_seen(self, device_id: str) -> None:
        """Update last_seen timestamp (called on heartbeat)."""
        await self.collection.update_one(
            {"device_id": device_id},
            {
                "$set": {
                    "last_seen": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "missed_heartbeats": 0,
                }
            },
        )

    async def increment_missed_heartbeats(self, device_id: str) -> int:
        """Increment missed heartbeat counter. Returns new count."""
        result = await self.collection.find_one_and_update(
            {"device_id": device_id},
            {
                "$inc": {"missed_heartbeats": 1},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
            return_document=True,
            projection={"_id": 0, "missed_heartbeats": 1},
        )
        return result["missed_heartbeats"] if result else 0

    async def set_credential(self, device_id: str, credential: dict) -> Optional[dict]:
        """Store the device credential record (hashed key only)."""
        return await self.update_fields(
            device_id,
            {
                "credential": credential,
                "provisioned_at": datetime.now(timezone.utc),
                "trust_state": "TRUSTED",
            },
        )

    async def revoke_credential(self, device_id: str) -> Optional[dict]:
        """Mark the credential as revoked."""
        return await self.update_fields(
            device_id,
            {"credential.is_revoked": True},
        )


def get_device_repository() -> DeviceRepository:
    """FastAPI dependency — returns a DeviceRepository instance."""
    return DeviceRepository(get_database())

