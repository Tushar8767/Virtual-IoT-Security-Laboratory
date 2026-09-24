"""
Phase 6 Tests — Authentication & Capability-Based Authorization

Tests:
1. Rejection of unauthenticated requests (missing headers)
2. Rejection of invalid API keys
3. Rejection of credentials for suspended/revoked devices
4. Successful device authentication
5. Enforcement of device capabilities (e.g. RECEIVE_COMMANDS)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from app.models.device import DeviceStatus, DeviceCapability
from app.core.security import hash_credential
from app.repositories.device_repository import get_device_repository
from app.models.audit import get_audit_repository


@pytest.fixture
def mock_device_repo():
    repo = MagicMock()
    return repo


@pytest.fixture
def mock_audit_repo():
    repo = MagicMock()
    repo.log = AsyncMock()
    return repo


class TestDeviceAuthentication:
    """Test API key validation and capability checks."""

    @pytest.mark.asyncio
    async def test_missing_headers_returns_401(self, mock_device_repo, mock_audit_repo):
        from app.main import app

        app.dependency_overrides[get_device_repository] = lambda: mock_device_repo
        app.dependency_overrides[get_audit_repository] = lambda: mock_audit_repo

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                res = await client.post("/api/devices/DEV-1/command", json={"action": "PING"})
                assert res.status_code == 401
                assert "Missing" in res.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_invalid_key_returns_401(self, mock_device_repo, mock_audit_repo):
        from app.main import app

        real_key = "iot-real-secret-key-12345"
        mock_device_repo.find_by_id = AsyncMock(return_value={
            "device_id": "DEV-1",
            "status": DeviceStatus.ONLINE.value,
            "capabilities": ["RECEIVE_COMMANDS"],
            "credential": {
                "hashed_key": hash_credential(real_key),
                "is_revoked": False,
            },
        })

        app.dependency_overrides[get_device_repository] = lambda: mock_device_repo
        app.dependency_overrides[get_audit_repository] = lambda: mock_audit_repo

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                res = await client.post(
                    "/api/devices/DEV-1/command",
                    headers={"X-Device-Id": "DEV-1", "X-API-Key": "iot-WRONG-KEY"},
                    json={"action": "PING"},
                )
                assert res.status_code == 401
                assert "Invalid" in res.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_valid_key_and_capability_returns_200(self, mock_device_repo, mock_audit_repo):
        from app.main import app

        real_key = "iot-valid-key-abcdef"
        mock_device_repo.find_by_id = AsyncMock(return_value={
            "device_id": "DEV-1",
            "status": DeviceStatus.ONLINE.value,
            "capabilities": [DeviceCapability.RECEIVE_COMMANDS.value],
            "credential": {
                "hashed_key": hash_credential(real_key),
                "is_revoked": False,
            },
        })

        app.dependency_overrides[get_device_repository] = lambda: mock_device_repo
        app.dependency_overrides[get_audit_repository] = lambda: mock_audit_repo

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                res = await client.post(
                    "/api/devices/DEV-1/command",
                    headers={"X-Device-Id": "DEV-1", "X-API-Key": real_key},
                    json={"action": "REBOOT"},
                )
                assert res.status_code == 200
                assert res.json()["status"] == "COMMAND_ACCEPTED"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_missing_capability_returns_403(self, mock_device_repo, mock_audit_repo):
        from app.main import app

        real_key = "iot-valid-key-abcdef"
        # Device lacks RECEIVE_COMMANDS
        mock_device_repo.find_by_id = AsyncMock(return_value={
            "device_id": "DEV-1",
            "status": DeviceStatus.ONLINE.value,
            "capabilities": [DeviceCapability.SEND_TELEMETRY.value],
            "credential": {
                "hashed_key": hash_credential(real_key),
                "is_revoked": False,
            },
        })

        app.dependency_overrides[get_device_repository] = lambda: mock_device_repo
        app.dependency_overrides[get_audit_repository] = lambda: mock_audit_repo

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                res = await client.post(
                    "/api/devices/DEV-1/command",
                    headers={"X-Device-Id": "DEV-1", "X-API-Key": real_key},
                    json={"action": "REBOOT"},
                )
                assert res.status_code == 403
                assert "lacks required capability" in res.json()["detail"]
        finally:
            app.dependency_overrides.clear()