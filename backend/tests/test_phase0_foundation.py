"""
Phase 0 Foundation Tests — Virtual IoT Security Laboratory

Tests:
1. Pydantic configuration and environment loading
2. Database connection and health status
3. MQTT client connection and health status
4. Security utilities (tokens, IDs, credential verification)
5. Root / health check endpoints
6. WebSocket connection and ping/pong
7. API route skeletons
"""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_device_credential_pair,
    verify_credential,
    safe_string_compare,
    generate_correlation_id,
    generate_event_id,
)
from app.core.database import connect_to_mongodb, close_mongodb_connection


@pytest.fixture(autouse=True)
async def setup_test_db():
    """Ensure database connection is initialized for tests."""
    await connect_to_mongodb()
    yield
    await close_mongodb_connection()


@pytest.fixture
def mock_mqtt_connected():
    """Mock MQTT as connected."""
    with patch(
        "app.core.mqtt_client.get_mqtt_status",
        return_value={
            "connected": True,
            "broker_host": "localhost",
            "broker_port": 1883,
            "listener_active": True,
        },
    ):
        yield


@pytest.fixture
async def app_client(mock_mqtt_connected):
    """
    Create a test client with mocked startup services.
    """
    with (
        patch("app.core.database.connect_to_mongodb", new_callable=AsyncMock),
        patch("app.core.database.close_mongodb_connection", new_callable=AsyncMock),
        patch("app.core.mqtt_client.connect_mqtt", new_callable=AsyncMock),
        patch("app.core.mqtt_client.disconnect_mqtt", new_callable=AsyncMock),
    ):
        from app.main import app
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            yield client


# ============================================================
# Test Groups
# ============================================================

class TestConfiguration:
    def test_settings_load_defaults(self):
        s = Settings()
        assert s.APP_NAME == "Virtual IoT Security Lab"
        assert s.BACKEND_PORT == 8000
        assert s.MQTT_BROKER_PORT == 1883
        assert s.MONGODB_DATABASE == "iot_security_lab"

    def test_cors_origins_parsed(self):
        s = Settings(BACKEND_CORS_ORIGINS="http://localhost:3000,http://localhost:5173")
        assert len(s.BACKEND_CORS_ORIGINS) == 2
        assert "http://localhost:3000" in s.BACKEND_CORS_ORIGINS

    def test_debug_coercion_from_string(self):
        s = Settings(DEBUG="true")
        assert s.DEBUG is True
        s2 = Settings(DEBUG="false")
        assert s2.DEBUG is False


class TestSecurityUtilities:
    def test_device_credentials_generation(self):
        plain, hashed = generate_device_credential_pair()
        assert plain.startswith("iot-")
        assert len(plain) == 52
        assert verify_credential(plain, hashed) is True
        assert verify_credential("iot-wrongkey", hashed) is False

    def test_jwt_create_and_decode(self):
        data = {"sub": "analyst-001", "role": "analyst"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "analyst-001"
        assert decoded["role"] == "analyst"

    def test_constant_time_compare(self):
        assert safe_string_compare("secret123", "secret123") is True
        assert safe_string_compare("secret123", "secret456") is False

    def test_id_generators(self):
        corr_id = generate_correlation_id()
        assert len(corr_id) == 36

        evt_id = generate_event_id()
        assert len(evt_id) == 36


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_200(self, app_client):
        response = await app_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "services" in data


class TestLabStatusEndpoint:
    @pytest.mark.asyncio
    async def test_lab_status_returns_200(self, app_client):
        response = await app_client.get("/api/lab/status")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_lab_status_contains_lab_status(self, app_client):
        response = await app_client.get("/api/lab/status")
        data = response.json()
        assert "lab_status" in data

    @pytest.mark.asyncio
    async def test_lab_status_contains_simulation(self, app_client):
        response = await app_client.get("/api/lab/status")
        data = response.json()
        assert "simulation" in data


class TestSkeletonRoutes:
    @pytest.mark.asyncio
    async def test_devices_list(self, app_client):
        response = await app_client.get("/api/devices/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_telemetry_list(self, app_client):
        response = await app_client.get("/api/telemetry/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_security_events(self, app_client):
        response = await app_client.get("/api/security/events")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_security_alerts(self, app_client):
        response = await app_client.get("/api/security/alerts")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_audit_list(self, app_client):
        response = await app_client.get("/api/audit/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_scenarios_list(self, app_client):
        response = await app_client.get("/api/scenarios/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_lab_start_skeleton(self, app_client):
        response = await app_client.post("/api/lab/start")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_lab_stop_skeleton(self, app_client):
        response = await app_client.post("/api/lab/stop")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_lab_reset_skeleton(self, app_client):
        response = await app_client.post("/api/lab/reset")
        assert response.status_code == 200