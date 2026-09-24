"""
Phase 0 Tests — Project Foundation

Tests:
1. Application starts and returns healthy root response
2. Health endpoint returns status
3. API docs are accessible
4. Lab status endpoint responds
5. All skeleton routes return expected structure
6. WebSocket endpoint accepts connections
7. Settings load correctly from environment
8. Security utilities work correctly
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def mock_db_connected():
    """Mock database as connected."""
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[])

    mock_collection = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=0)
    mock_collection.find.return_value = mock_cursor

    mock_db.__getitem__.return_value = mock_collection
    mock_db.devices = mock_collection
    mock_db.audit_logs = mock_collection
    with (
        patch(
            "app.core.database.get_database_status",
            new_callable=AsyncMock,
            return_value={"connected": True, "database": "iot_security_lab", "ping": True},
        ),
        patch("app.core.database.get_database", return_value=mock_db),
    ):
        yield mock_db


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
async def app_client(mock_db_connected, mock_mqtt_connected):
    """
    Create a test client with mocked startup services.
    Bypasses real DB/MQTT connections for unit tests.
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


class TestRootEndpoint:
    """Test the root / endpoint."""

    async def test_root_returns_200(self, app_client):
        response = await app_client.get("/")
        assert response.status_code == 200

    async def test_root_contains_name(self, app_client):
        response = await app_client.get("/")
        data = response.json()
        assert "name" in data
        assert "Virtual IoT Security Lab" in data["name"]

    async def test_root_contains_version(self, app_client):
        response = await app_client.get("/")
        data = response.json()
        assert "version" in data

    async def test_root_contains_docs_link(self, app_client):
        response = await app_client.get("/")
        data = response.json()
        assert "docs" in data


class TestHealthEndpoint:
    """Test the /api/health endpoint."""

    async def test_health_returns_200(self, app_client):
        response = await app_client.get("/api/health")
        assert response.status_code == 200

    async def test_health_contains_status(self, app_client):
        response = await app_client.get("/api/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ("healthy", "degraded")

    async def test_health_contains_services(self, app_client):
        response = await app_client.get("/api/health")
        data = response.json()
        assert "services" in data
        assert "database" in data["services"]
        assert "mqtt" in data["services"]

    async def test_health_healthy_when_services_up(self, app_client):
        response = await app_client.get("/api/health")
        data = response.json()
        assert data["status"] == "healthy"


class TestLabStatusEndpoint:
    """Test the /api/lab/status endpoint."""

    async def test_lab_status_returns_200(self, app_client):
        response = await app_client.get("/api/lab/status")
        assert response.status_code == 200

    async def test_lab_status_contains_lab_status(self, app_client):
        response = await app_client.get("/api/lab/status")
        data = response.json()
        assert "lab_status" in data
        assert data["lab_status"] in ("running", "degraded")

    async def test_lab_status_contains_simulation(self, app_client):
        response = await app_client.get("/api/lab/status")
        data = response.json()
        assert "simulation" in data


class TestSkeletonRoutes:
    """Test that all Phase 0 skeleton routes are reachable."""

    async def test_devices_list(self, app_client):
        response = await app_client.get("/api/devices/")
        assert response.status_code == 200
        data = response.json()
        assert "devices" in data

    async def test_telemetry_list(self, app_client):
        response = await app_client.get("/api/telemetry/")
        assert response.status_code == 200

    async def test_security_events(self, app_client):
        response = await app_client.get("/api/security/events")
        assert response.status_code == 200

    async def test_security_alerts(self, app_client):
        response = await app_client.get("/api/security/alerts")
        assert response.status_code == 200

    async def test_scenarios_list(self, app_client):
        response = await app_client.get("/api/scenarios/")
        assert response.status_code == 200

    async def test_audit_list(self, app_client):
        response = await app_client.get("/api/audit/")
        assert response.status_code == 200

    async def test_lab_start_skeleton(self, app_client):
        response = await app_client.post("/api/lab/start")
        assert response.status_code == 200

    async def test_lab_stop_skeleton(self, app_client):
        response = await app_client.post("/api/lab/stop")
        assert response.status_code == 200

    async def test_lab_reset_skeleton(self, app_client):
        response = await app_client.post("/api/lab/reset")
        assert response.status_code == 200


class TestApiDocs:
    """Test that OpenAPI documentation is accessible."""

    async def test_openapi_json(self, app_client):
        response = await app_client.get("/api/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data

    async def test_docs_page(self, app_client):
        response = await app_client.get("/api/docs")
        assert response.status_code == 200


class TestSettingsConfiguration:
    """Test that settings load correctly."""

    def test_settings_has_app_name(self):
        from app.core.config import settings
        assert settings.APP_NAME == "Virtual IoT Security Lab"

    def test_settings_has_mongodb_uri(self):
        from app.core.config import settings
        assert settings.MONGODB_URI is not None
        assert "mongodb" in settings.MONGODB_URI

    def test_settings_has_mqtt_config(self):
        from app.core.config import settings
        assert settings.MQTT_BROKER_HOST is not None
        assert settings.MQTT_BROKER_PORT == 1883

    def test_settings_has_security_thresholds(self):
        from app.core.config import settings
        assert settings.AUTH_FAILURE_THRESHOLD > 0
        assert settings.HEARTBEAT_TIMEOUT_SECONDS > 0


class TestSecurityUtilities:
    """Test security utility functions."""

    def test_hash_credential_produces_hash(self):
        from app.core.security import hash_credential
        hashed = hash_credential("my_secret_key")
        assert hashed != "my_secret_key"
        assert len(hashed) > 20

    def test_verify_credential_correct(self):
        from app.core.security import hash_credential, verify_credential
        plain = "test_device_key_123"
        hashed = hash_credential(plain)
        assert verify_credential(plain, hashed) is True

    def test_verify_credential_incorrect(self):
        from app.core.security import hash_credential, verify_credential
        plain = "correct_key"
        hashed = hash_credential(plain)
        assert verify_credential("wrong_key", hashed) is False

    def test_generate_device_api_key_format(self):
        from app.core.security import generate_device_api_key
        key = generate_device_api_key()
        assert key.startswith("iot-")
        assert len(key) == 4 + 48  # "iot-" + 48 hex chars

    def test_generate_unique_keys(self):
        from app.core.security import generate_device_api_key
        keys = {generate_device_api_key() for _ in range(10)}
        assert len(keys) == 10  # All unique

    def test_generate_correlation_id_is_uuid(self):
        from app.core.security import generate_correlation_id
        import uuid
        cid = generate_correlation_id()
        # Should be a valid UUID
        uuid.UUID(cid)

    def test_safe_string_compare_equal(self):
        from app.core.security import safe_string_compare
        assert safe_string_compare("abc123", "abc123") is True

    def test_safe_string_compare_not_equal(self):
        from app.core.security import safe_string_compare
        assert safe_string_compare("abc123", "xyz789") is False

    def test_credential_pair_generation(self):
        from app.core.security import generate_device_credential_pair, verify_credential
        plain, hashed = generate_device_credential_pair()
        assert plain.startswith("iot-")
        assert verify_credential(plain, hashed) is True

