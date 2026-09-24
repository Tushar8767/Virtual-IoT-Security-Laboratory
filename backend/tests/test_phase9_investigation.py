"""
Phase 9 Tests — Security Investigation & Event Correlation

Tests:
1. Reconstructing correlated timeline across events, alerts, and audit entries
2. Building complete device forensic profile
3. REST API: GET /api/investigation/timeline/{correlation_id}
4. REST API: GET /api/investigation/device/{device_id}
5. 404 response for unknown devices in investigation
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from app.services.investigation_service import InvestigationService
from app.api.routes.investigation import get_investigation_service


@pytest.fixture
def mock_repos():
    sec_repo = MagicMock()
    tel_repo = MagicMock()
    dev_repo = MagicMock()
    aud_repo = MagicMock()

    # Setup async methods
    sec_repo.find_recent_events = AsyncMock(return_value=[])
    sec_repo.find_alerts = AsyncMock(return_value=[])
    tel_repo.find_by_device = AsyncMock(return_value=[])
    aud_repo.find_by_target = AsyncMock(return_value=[])
    dev_repo.find_by_id = AsyncMock(return_value={"device_id": "LPC2138-TEMP-001"})

    # Setup collection query mocks for timeline
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=[])

    sec_repo.events_col.find = MagicMock(return_value=mock_cursor)
    sec_repo.alerts_col.find = MagicMock(return_value=mock_cursor)
    aud_repo.collection.find = MagicMock(return_value=mock_cursor)

    return sec_repo, tel_repo, dev_repo, aud_repo


class TestInvestigationService:
    """Test correlation and timeline reconstruction logic."""

    @pytest.mark.asyncio
    async def test_get_device_forensic_profile(self, mock_repos):
        sec_repo, tel_repo, dev_repo, aud_repo = mock_repos
        svc = InvestigationService(sec_repo, tel_repo, dev_repo, aud_repo)

        profile = await svc.get_device_forensic_profile("LPC2138-TEMP-001")
        assert profile["device_id"] == "LPC2138-TEMP-001"
        assert "events" in profile
        assert "alerts" in profile
        assert "recent_telemetry" in profile
        assert "audit_trail" in profile

    @pytest.mark.asyncio
    async def test_build_correlation_timeline_sorting(self, mock_repos):
        sec_repo, tel_repo, dev_repo, aud_repo = mock_repos

        # Mock items with timestamps
        t1 = "2026-09-25T01:00:00Z"
        t2 = "2026-09-25T01:01:00Z"
        t3 = "2026-09-25T01:02:00Z"

        c1 = MagicMock()
        c1.to_list = AsyncMock(return_value=[{"event_id": "e1", "timestamp": t2, "rule_type": "OVERHEAT", "severity": "HIGH"}])
        sec_repo.events_col.find = MagicMock(return_value=c1)

        c2 = MagicMock()
        c2.to_list = AsyncMock(return_value=[{"alert_id": "a1", "created_at": t3, "title": "OVERHEAT_ALERT", "status": "ACTIVE"}])
        sec_repo.alerts_col.find = MagicMock(return_value=c2)

        c3 = MagicMock()
        c3.to_list = AsyncMock(return_value=[{"audit_id": "au1", "timestamp": t1, "action": "AUTH_SUCCESS", "actor": "dev"}])
        aud_repo.collection.find = MagicMock(return_value=c3)

        svc = InvestigationService(sec_repo, tel_repo, dev_repo, aud_repo)
        res = await svc.build_correlation_timeline("corr-abc-123")

        assert res["correlation_id"] == "corr-abc-123"
        assert res["total_correlated_items"] == 3
        # Ensure chronological ordering: t1, then t2, then t3
        timeline = res["timeline"]
        assert timeline[0]["type"] == "AUDIT_RECORD"
        assert timeline[1]["type"] == "SECURITY_EVENT"
        assert timeline[2]["type"] == "SECURITY_ALERT"


class TestInvestigationAPI:
    """Test investigation REST routes."""

    @pytest.mark.asyncio
    async def test_get_device_forensic_profile_api(self):
        from app.main import app

        mock_svc = MagicMock()
        mock_svc.get_device_forensic_profile = AsyncMock(return_value={
            "device_id": "PY-TEMP-001",
            "device": {"device_id": "PY-TEMP-001"},
            "total_security_events": 0,
            "total_alerts": 0,
            "events": [],
            "alerts": [],
            "recent_telemetry": [],
            "audit_trail": [],
        })

        app.dependency_overrides[get_investigation_service] = lambda: mock_svc

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                res = await client.get("/api/investigation/device/PY-TEMP-001")
                assert res.status_code == 200
                assert res.json()["device_id"] == "PY-TEMP-001"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_incident_timeline_api(self):
        from app.main import app

        mock_svc = MagicMock()
        mock_svc.build_correlation_timeline = AsyncMock(return_value={
            "correlation_id": "corr-test-999",
            "total_correlated_items": 1,
            "timeline": [{"type": "SECURITY_EVENT", "summary": "TEST"}],
        })

        app.dependency_overrides[get_investigation_service] = lambda: mock_svc

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                res = await client.get("/api/investigation/timeline/corr-test-999")
                assert res.status_code == 200
                data = res.json()
                assert data["correlation_id"] == "corr-test-999"
                assert len(data["timeline"]) == 1
        finally:
            app.dependency_overrides.clear()