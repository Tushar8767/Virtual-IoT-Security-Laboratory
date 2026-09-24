"""
Security Repository — MongoDB Persistence

Handles storage, lookup, and updates for:
- security_events collection
- alerts collection
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import structlog
from app.core.database import get_database

logger = structlog.get_logger(__name__)


class SecurityRepository:
    """Async repository for security events and alerts."""

    def __init__(self, db=None):
        self.db = db if db is not None else get_database()
        self.events_col = self.db["security_events"]
        self.alerts_col = self.db["alerts"]

    # --- Events ---
    async def insert_event(self, event_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a security event."""
        if "timestamp" not in event_doc:
            event_doc["timestamp"] = datetime.now(timezone.utc)
        await self.events_col.insert_one(event_doc)
        return event_doc

    async def find_recent_events(self, limit: int = 100, device_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent security events."""
        query = {"device_id": device_id} if device_id else {}
        cursor = self.events_col.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)

    # --- Alerts ---
    async def insert_alert(self, alert_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new security alert."""
        now = datetime.now(timezone.utc)
        alert_doc["created_at"] = alert_doc.get("created_at", now)
        alert_doc["updated_at"] = now
        await self.alerts_col.insert_one(alert_doc)
        return alert_doc

    async def find_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        device_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Query security alerts with filters."""
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status
        if severity:
            query["severity"] = severity
        if device_id:
            query["device_id"] = device_id

        cursor = self.alerts_col.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def update_alert_status(self, alert_id: str, new_status: str) -> Optional[Dict[str, Any]]:
        """Update an alert's status (ACTIVE -> INVESTIGATING -> RESOLVED)."""
        now = datetime.now(timezone.utc)
        result = await self.alerts_col.find_one_and_update(
            {"alert_id": alert_id},
            {"$set": {"status": new_status, "updated_at": now}},
            return_document=True,
            projection={"_id": 0},
        )
        return result

    async def get_security_summary(self) -> Dict[str, Any]:
        """Summary metrics for the dashboard."""
        active_count = await self.alerts_col.count_documents({"status": "ACTIVE"})
        total_alerts = await self.alerts_col.count_documents({})
        total_events = await self.events_col.count_documents({})
        return {
            "active_alerts": active_count,
            "total_alerts": total_alerts,
            "total_events": total_events,
        }


def get_security_repository() -> SecurityRepository:
    return SecurityRepository(get_database())