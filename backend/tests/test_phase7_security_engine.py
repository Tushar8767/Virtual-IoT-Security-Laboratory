"""
Phase 7 Tests — Security Detection Engine & Alerts

Tests:
1. Detection of out-of-bounds values (VALUE_OUT_OF_BOUNDS)
2. Normal values do not trigger false alerts
3. Escalation of security events to security alerts
4. REST API: GET /api/security/events
5. REST API: GET /api/security/alerts
6. REST API: PATCH /api/security/alerts/{alert_id} (alert triage status update)
7. REST API: GET /api/security/summary
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.models.security import Severity, RuleType, AlertStatus
from app.security.engine import SecurityDetectionEngine
from app.repositories.security_repository import SecurityRepository, get_security_repository


@pytest.fixture
def mock_security_repo():
    repo = MagicMock(spec=SecurityRepository)
    repo.insert_event = AsyncMock()
    repo.insert_alert = AsyncMock()
    repo.find_recent_events = AsyncMock(return_value=[])
    repo.find_alerts = AsyncMock(return_value=[])
    repo.update_alert_status = AsyncMock()
    repo.get_security_summary = AsyncMock(return_value={
        "active_alerts": 2,
        "total_alerts": 5,
        "total_events": 10,
    })
    return repo


class TestSecurityDetectionEngine:
    """Test rule evaluations and alert generation."""

    @pytest.mark.asyncio
    async def test_detects_temperature_out_of_bounds(self, mock_security_repo):
        engine = SecurityDetectionEngine(mock_security_repo)
        payload = {
            "device_id": "LPC2138-TEMP-001",
            "values": {"temperature_c": 95.5},
            "correlation_id": "corr-123",
        }

        with patch("app.security.engine.broadcast_event", new_callable=AsyncMock) as mock_broadcast:
            alert = await engine.evaluate_telemetry(payload)
            assert alert is not None
            assert alert["rule_type"] == RuleType.VALUE_OUT_OF_BOUNDS.value
            assert alert["severity"] == Severity.CRITICAL.value
            assert alert["status"] == AlertStatus.ACTIVE.value

            mock_security_repo.insert_event.assert_awaited_once()
            mock_security_repo.insert_alert.assert_awaited_once()
            assert mock_broadcast.await_count >= 1

    @pytest.mark.asyncio
    async def test_normal_temperature_does_not_trigger_alert(self, mock_security_repo):
        engine = SecurityDetectionEngine(mock_security_repo)
        payload = {
            "device_id": "PY-TEMP-001",
            "values": {"temperature_c": 24.5},
        }

        alert = await engine.evaluate_telemetry(payload)
        assert alert is None
        mock_security_repo.insert_event.assert_not_awaited()
        mock_security_repo.insert_alert.assert_not_awaited()


class TestSecurityAPI:
    """Test security REST endpoints."""

    @pytest.mark.asyncio
    async def test_list_security_events_endpoint(self, mock_security_repo):
        from app.main import app

        mock_security_repo.find_recent_events = AsyncMock(return_value=[
            {"event_id": "evt-1", "rule_type": "VALUE_OUT_OF_BOUNDS", "severity": "HIGH"},
        ])

        app.dependency_overrides[get_security_repository] = lambda: mock_security_repo

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                res = await client.get("/api/security/events")
                assert res.status_code == 200
                data = res.json()
                assert data["count"] == 1
                assert data["events"][0]["event_id"] == "evt-1"
        finally:
            app.dependency_overrides.pop(get_security_repository, None)

    @pytest.mark.asyncio
    async def test_list_security_alerts_endpoint(self, mock_security_repo):
        from app.main import app

        mock_security_repo.find_alerts = AsyncMock(return_value=[
            {"alert_id": "alt-1", "severity": "CRITICAL", "status": "ACTIVE"},
        ])

        app.dependency_overrides[get_security_repository] = lambda: mock_security_repo

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                res = await client.get("/api/security/alerts?status=ACTIVE")
                assert res.status_code == 200
                data = res.json()
                assert data["count"] == 1
                assert data["alerts"][0]["alert_id"] == "alt-1"
        finally:
            app.dependency_overrides.pop(get_security_repository, None)

    @pytest.mark.asyncio
    async def test_update_alert_status_endpoint(self, mock_security_repo):
        from app.main import app

        mock_security_repo.update_alert_status = AsyncMock(return_value={
            "alert_id": "alt-1",
            "status": "RESOLVED",
        })

        app.dependency_overrides[get_security_repository] = lambda: mock_security_repo

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                res = await client.patch(
                    "/api/security/alerts/alt-1",
                    json={"new_status": "RESOLVED"},
                )
                assert res.status_code == 200
                assert res.json()["status"] == "RESOLVED"
        finally:
            app.dependency_overrides.pop(get_security_repository, None)

    @pytest.mark.asyncio
    async def test_get_security_summary_endpoint(self, mock_security_repo):
        from app.main import app

        app.dependency_overrides[get_security_repository] = lambda: mock_security_repo

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                res = await client.get("/api/security/summary")
                assert res.status_code == 200
                data = res.json()
                assert data["active_alerts"] == 2
                assert data["total_alerts"] == 5
        finally:
            app.dependency_overrides.pop(get_security_repository, None)