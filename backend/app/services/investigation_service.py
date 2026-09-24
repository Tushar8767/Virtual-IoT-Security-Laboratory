"""
Investigation Service — Incident Correlation & Timeline Reconstruction

Correlates security events, telemetry readings, and audit trails
to build an end-to-end incident forensic timeline.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import structlog

from app.repositories.security_repository import SecurityRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.repositories.device_repository import DeviceRepository
from app.models.audit import AuditRepository

logger = structlog.get_logger(__name__)


class InvestigationService:
    """
    Forensic investigation and incident timeline reconstruction.
    """

    def __init__(
        self,
        security_repo: SecurityRepository,
        telemetry_repo: TelemetryRepository,
        device_repo: DeviceRepository,
        audit_repo: AuditRepository,
    ):
        self.security_repo = security_repo
        self.telemetry_repo = telemetry_repo
        self.device_repo = device_repo
        self.audit_repo = audit_repo

    async def get_device_forensic_profile(self, device_id: str) -> Dict[str, Any]:
        """
        Gathers complete forensic history for a device.
        """
        device = await self.device_repo.find_by_id(device_id)
        events = await self.security_repo.find_recent_events(limit=50, device_id=device_id)
        alerts = await self.security_repo.find_alerts(limit=50, device_id=device_id)
        telemetry = await self.telemetry_repo.find_by_device(device_id, limit=50)
        audit_trail = await self.audit_repo.find_by_target(device_id, limit=50)

        return {
            "device_id": device_id,
            "device": device,
            "total_security_events": len(events),
            "total_alerts": len(alerts),
            "events": events,
            "alerts": alerts,
            "recent_telemetry": telemetry,
            "audit_trail": audit_trail,
        }

    async def build_correlation_timeline(self, correlation_id: str) -> Dict[str, Any]:
        """
        Reconstructs chronological timeline for a specific correlation ID.
        """
        timeline_items: List[Dict[str, Any]] = []

        # Find matching events
        events = await self.security_repo.events_col.find(
            {"correlation_id": correlation_id}, {"_id": 0}
        ).to_list(length=100)

        for e in events:
            timeline_items.append({
                "type": "SECURITY_EVENT",
                "timestamp": e.get("timestamp"),
                "summary": f"{e.get('rule_type')} ({e.get('severity')})",
                "details": e,
            })

        # Find matching alerts
        alerts = await self.security_repo.alerts_col.find(
            {"correlation_id": correlation_id}, {"_id": 0}
        ).to_list(length=50)

        for a in alerts:
            timeline_items.append({
                "type": "SECURITY_ALERT",
                "timestamp": a.get("created_at"),
                "summary": f"ALERT: {a.get('title')} [{a.get('status')}]",
                "details": a,
            })

        # Find matching audit records
        audits = await self.audit_repo.collection.find(
            {"correlation_id": correlation_id}, {"_id": 0}
        ).to_list(length=100)

        for ad in audits:
            timeline_items.append({
                "type": "AUDIT_RECORD",
                "timestamp": ad.get("timestamp"),
                "summary": f"AUDIT: {ad.get('action')} by {ad.get('actor')}",
                "details": ad,
            })

        # Sort chronologically
        timeline_items.sort(
            key=lambda x: str(x.get("timestamp") or ""),
            reverse=False,
        )

        return {
            "correlation_id": correlation_id,
            "total_correlated_items": len(timeline_items),
            "timeline": timeline_items,
        }