"""
Phase 4 Tests — Telemetry Pipeline & Ingestion

Tests:
1. Telemetry repository insertion and retrieval
2. Telemetry pipeline ingestion, persistence, and state update
3. Device transitions from PROVISIONED to ONLINE upon first telemetry
4. REST API: GET /api/telemetry/latest
5. REST API: GET /api/telemetry/device/{device_id}
6. REST API: POST /api/telemetry/ingest
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.models.device import DeviceStatus
from app.telemetry.pipeline import TelemetryPipeline
from app.repositories.telemetry_repository import (
    TelemetryRepository,
    get_telemetry_repository,
)
from app.api.routes.telemetry import get_pipeline


@pytest.fixture
def mock_telemetry_repo():
    repo = MagicMock(spec=TelemetryRepository)
    repo.insert = AsyncMock(return_value={"status": "inserted"})
    repo.find_by_device = AsyncMock(return_value=[])
    repo.get_latest_fleet_telemetry = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_device_repo():
    repo = MagicMock()
    repo.update_last_seen = AsyncMock()
    repo.update_status = AsyncMock()
    repo.find_by_id = AsyncMock(return_value={
        "device_id": "TEST-DEVICE-01",
        "status": DeviceStatus.PROVISIONED.value,
    })
    return repo


class TestTelemetryPipeline:
    """Test the telemetry ingestion pipeline."""

    @pytest.mark.asyncio
    async def test_pipeline_persists_and_updates_status(self, mock_telemetry_repo, mock_device_repo):
        pipeline = TelemetryPipeline(mock_telemetry_repo, mock_device_repo)
        payload = {
            "device_id": "TEST-DEVICE-01",
            "device_type": "temperature_sensor",
            "values": {"temperature_c": 24.5},
            "sequence_number": 1,
        }

        with patch("app.telemetry.pipeline.broadcast_event", new_callable=AsyncMock) as mock_broadcast:
            success, reason = await pipeline.process_telemetry(payload)
            assert success is True
            assert reason == "SUCCESS"

            # Verify persisted
            mock_telemetry_repo.insert.assert_awaited_once_with(payload)

            # Verify device last_seen was updated
            mock_device_repo.update_last_seen.assert_awaited_once_with("TEST-DEVICE-01")

            # Verify transitioned PROVISIONED -> ONLINE
            mock_device_repo.update_status.assert_awaited_once_with(
                "TEST-DEVICE-01", DeviceStatus.ONLINE.value
            )

            # Verify broadcast was called
            assert mock_broadcast.await_count >= 1

    @pytest.mark.asyncio
    async def test_pipeline_rejects_missing_device_id(self, mock_telemetry_repo, mock_device_repo):
        pipeline = TelemetryPipeline(mock_telemetry_repo, mock_device_repo)
        success, reason = await pipeline.process_telemetry({"values": {}})
        assert success is False
        assert reason == "MISSING_DEVICE_ID"


class TestTelemetryAPI:
    """Test telemetry REST endpoints using FastAPI dependency overrides."""

    @pytest.mark.asyncio
    async def test_ingest_telemetry_endpoint(self):
        from app.main import app

        payload = {
            "device_id": "TEST-HTTP-01",
            "device_type": "motion_sensor",
            "values": {"motion_detected": True},
        }

        mock_pipeline = MagicMock()
        mock_pipeline.process_telemetry = AsyncMock(return_value=(True, "SUCCESS"))

        app.dependency_overrides[get_pipeline] = lambda: mock_pipeline

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                res = await client.post("/api/telemetry/ingest", json=payload)
                assert res.status_code == 201
                assert res.json()["status"] == "INGESTED"
        finally:
            app.dependency_overrides.pop(get_pipeline, None)

    @pytest.mark.asyncio
    async def test_get_latest_telemetry_endpoint(self):
        from app.main import app

        mock_repo = MagicMock()
        mock_repo.get_latest_fleet_telemetry = AsyncMock(return_value=[
            {"device_id": "DEV-1", "values": {"temp": 22.0}},
            {"device_id": "DEV-2", "values": {"temp": 24.0}},
        ])

        app.dependency_overrides[get_telemetry_repository] = lambda: mock_repo

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                res = await client.get("/api/telemetry/latest")
                assert res.status_code == 200
                data = res.json()
                assert data["count"] == 2
                assert len(data["telemetry"]) == 2
        finally:
            app.dependency_overrides.pop(get_telemetry_repository, None)

    @pytest.mark.asyncio
    async def test_get_device_telemetry_endpoint(self):
        from app.main import app

        mock_repo = MagicMock()
        mock_repo.find_by_device = AsyncMock(return_value=[
            {"device_id": "DEV-1", "sequence_number": 1, "values": {"temp": 22.0}},
        ])

        app.dependency_overrides[get_telemetry_repository] = lambda: mock_repo

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                res = await client.get("/api/telemetry/device/DEV-1")
                assert res.status_code == 200
                data = res.json()
                assert data["device_id"] == "DEV-1"
                assert len(data["telemetry"]) == 1
        finally:
            app.dependency_overrides.pop(get_telemetry_repository, None)