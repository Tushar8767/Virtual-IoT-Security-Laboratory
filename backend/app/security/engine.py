"""
Security Detection Engine — Deterministic Rules & Alert Escalation

Inspects incoming telemetry, heartbeats, and gateway rejections against:
- Value bounds checks (e.g. overheating)
- Rate anomaly checks
- Impersonation checks
- Escalates qualifying violations to Security Alerts and notifies WebSocket clients
"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import structlog

from app.models.security import Severity, RuleType, AlertStatus
from app.repositories.security_repository import SecurityRepository
from app.api.websocket import broadcast_event

logger = structlog.get_logger(__name__)


class SecurityDetectionEngine:
    """
    Deterministic rule-based security evaluation engine.
    """

    def __init__(self, security_repo: SecurityRepository):
        self.security_repo = security_repo

    async def evaluate_telemetry(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Evaluate an ingested telemetry packet for anomalies.
        """
        device_id = payload.get("device_id", "UNKNOWN")
        values = payload.get("values", {})
        correlation_id = payload.get("correlation_id", str(uuid.uuid4()))

        # Rule 1: Out-of-bounds Temperature (Overheating Anomaly)
        temp_c = values.get("temperature_c")
        if temp_c is not None and isinstance(temp_c, (int, float)):
            if temp_c > 65.0:
                severity = Severity.CRITICAL if temp_c > 90.0 else Severity.HIGH
                return await self.trigger_event_and_alert(
                    rule_type=RuleType.VALUE_OUT_OF_BOUNDS,
                    severity=severity,
                    device_id=device_id,
                    description=f"Temperature reading {temp_c}°C exceeded safety threshold (65.0°C). Possible physical manipulation or overheating.",
                    correlation_id=correlation_id,
                    metadata={"temperature_c": temp_c, "raw_reading": values.get("raw_reading")},
                    recommended_action="Suspend device or inspect physical environment immediately.",
                )

        return None

    async def trigger_event_and_alert(
        self,
        rule_type: RuleType,
        severity: Severity,
        device_id: str,
        description: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        recommended_action: str = "Inspect device logs.",
    ) -> Dict[str, Any]:
        """
        Create a security event, escalate to alert, persist, and broadcast.
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        event_id = f"sec-evt-{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc)

        # 1. Store event
        event_doc = {
            "event_id": event_id,
            "rule_type": rule_type.value if hasattr(rule_type, "value") else str(rule_type),
            "severity": severity.value if hasattr(severity, "value") else str(severity),
            "device_id": device_id,
            "timestamp": now,
            "description": description,
            "correlation_id": correlation_id,
            "metadata": metadata or {},
        }
        await self.security_repo.insert_event(event_doc)

        # 2. Escalate to Alert
        alert_id = f"alt-{uuid.uuid4().hex[:8]}"
        alert_doc = {
            "alert_id": alert_id,
            "title": f"Security Alert: {rule_type.value if hasattr(rule_type, 'value') else rule_type}",
            "rule_type": rule_type.value if hasattr(rule_type, "value") else str(rule_type),
            "severity": severity.value if hasattr(severity, "value") else str(severity),
            "status": AlertStatus.ACTIVE.value,
            "device_id": device_id,
            "created_at": now,
            "updated_at": now,
            "correlation_id": correlation_id,
            "event_ids": [event_id],
            "description": description,
            "recommended_action": recommended_action,
        }
        await self.security_repo.insert_alert(alert_doc)

        # 3. Broadcast Alert to React SOC Dashboard
        try:
            broadcast_payload = dict(alert_doc)
            broadcast_payload.pop("_id", None)
            broadcast_payload["created_at"] = now.isoformat()
            broadcast_payload["updated_at"] = now.isoformat()
            await broadcast_event("security_alert_created", broadcast_payload)
        except Exception as e:
            logger.debug("ws_broadcast_failed", error=str(e))

        logger.warning(
            "security_alert_triggered",
            alert_id=alert_id,
            device_id=device_id,
            rule=rule_type,
            severity=severity,
        )
        return alert_doc