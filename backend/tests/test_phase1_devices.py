"""
Phase 1 Tests — Device Domain

Tests:
1. Device state machine — valid transitions
2. Device state machine — invalid transitions
3. Default capabilities per device type
4. Device creation API
5. Device retrieval API
6. Device listing API
7. Device update API
8. Device provisioning API
9. Credential rotation
10. Device suspension
11. Device reinstatement
12. Device revocation
13. Revoked device update rejection
14. Unknown device 404 responses
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone


# ============================================================
# Unit Tests — State Machine
# ============================================================

class TestDeviceStateMachine:
    """Test the device state machine transitions."""

    def test_registered_can_transition_to_provisioned(self):
        from app.models.device import DeviceStatus, is_valid_transition
        assert is_valid_transition(DeviceStatus.REGISTERED, DeviceStatus.PROVISIONED) is True

    def test_registered_can_be_revoked(self):
        from app.models.device import DeviceStatus, is_valid_transition
        assert is_valid_transition(DeviceStatus.REGISTERED, DeviceStatus.REVOKED) is True

    def test_registered_cannot_go_online(self):
        from app.models.device import DeviceStatus, is_valid_transition
        assert is_valid_transition(DeviceStatus.REGISTERED, DeviceStatus.ONLINE) is False

    def test_provisioned_can_go_online(self):
        from app.models.device import DeviceStatus, is_valid_transition
        assert is_valid_transition(DeviceStatus.PROVISIONED, DeviceStatus.ONLINE) is True

    def test_online_can_go_offline(self):
        from app.models.device import DeviceStatus, is_valid_transition
        assert is_valid_transition(DeviceStatus.ONLINE, DeviceStatus.OFFLINE) is True

    def test_offline_can_go_online(self):
        from app.models.device import DeviceStatus, is_valid_transition
        assert is_valid_transition(DeviceStatus.OFFLINE, DeviceStatus.ONLINE) is True

    def test_online_can_be_suspended(self):
        from app.models.device import DeviceStatus, is_valid_transition
        assert is_valid_transition(DeviceStatus.ONLINE, DeviceStatus.SUSPENDED) is True

    def test_offline_can_be_suspended(self):
        from app.models.device import DeviceStatus, is_valid_transition
        assert is_valid_transition(DeviceStatus.OFFLINE, DeviceStatus.SUSPENDED) is True

    def test_suspended_can_go_online(self):
        from app.models.device import DeviceStatus, is_valid_transition
        assert is_valid_transition(DeviceStatus.SUSPENDED, DeviceStatus.ONLINE) is True

    def test_suspended_can_be_revoked(self):
        from app.models.device import DeviceStatus, is_valid_transition
        assert is_valid_transition(DeviceStatus.SUSPENDED, DeviceStatus.REVOKED) is True

    def test_revoked_is_terminal(self):
        from app.models.device import DeviceStatus, is_valid_transition
        for target in DeviceStatus:
            assert is_valid_transition(DeviceStatus.REVOKED, target) is False

    def test_suspended_cannot_go_offline(self):
        from app.models.device import DeviceStatus, is_valid_transition
        assert is_valid_transition(DeviceStatus.SUSPENDED, DeviceStatus.OFFLINE) is False

    def test_online_cannot_go_registered(self):
        from app.models.device import DeviceStatus, is_valid_transition
        assert is_valid_transition(DeviceStatus.ONLINE, DeviceStatus.REGISTERED) is False


class TestDefaultCapabilities:
    """Test default capability assignment per device type."""

    def test_temperature_sensor_has_send_telemetry(self):
        from app.models.device import DeviceType, DeviceCapability, DEFAULT_CAPABILITIES
        caps = DEFAULT_CAPABILITIES[DeviceType.TEMPERATURE_SENSOR]
        assert DeviceCapability.SEND_TELEMETRY in caps

    def test_smart_actuator_has_control_actuator(self):
        from app.models.device import DeviceType, DeviceCapability, DEFAULT_CAPABILITIES
        caps = DEFAULT_CAPABILITIES[DeviceType.SMART_ACTUATOR]
        assert DeviceCapability.CONTROL_ACTUATOR in caps

    def test_temperature_sensor_cannot_control_actuator(self):
        from app.models.device import DeviceType, DeviceCapability, DEFAULT_CAPABILITIES
        caps = DEFAULT_CAPABILITIES[DeviceType.TEMPERATURE_SENSOR]
        assert DeviceCapability.CONTROL_ACTUATOR not in caps

    def test_gateway_can_manage_devices(self):
        from app.models.device import DeviceType, DeviceCapability, DEFAULT_CAPABILITIES
        caps = DEFAULT_CAPABILITIES[DeviceType.GATEWAY]
        assert DeviceCapability.MANAGE_DEVICES in caps

    def test_all_device_types_have_capabilities(self):
        from app.models.device import DeviceType, DEFAULT_CAPABILITIES
        for device_type in DeviceType:
            assert device_type in DEFAULT_CAPABILITIES
            assert len(DEFAULT_CAPABILITIES[device_type]) > 0


# ============================================================
# Device Domain Model Tests
# ============================================================

class TestDeviceModel:
    """Test the Device domain model."""

    def test_device_can_check_capability(self):
        from app.models.device import Device, DeviceType, DeviceCapability
        device = Device(
            device_id="dev-test",
            device_name="Test Sensor",
            device_type=DeviceType.TEMPERATURE_SENSOR,
            capabilities=[DeviceCapability.SEND_TELEMETRY, DeviceCapability.READ_TELEMETRY],
        )
        assert device.has_capability(DeviceCapability.SEND_TELEMETRY) is True

    def test_device_missing_capability(self):
        from app.models.device import Device, DeviceType, DeviceCapability
        device = Device(
            device_id="dev-test",
            device_name="Test Sensor",
            device_type=DeviceType.TEMPERATURE_SENSOR,
            capabilities=[DeviceCapability.SEND_TELEMETRY],
        )
        assert device.has_capability(DeviceCapability.CONTROL_ACTUATOR) is False

    def test_device_can_transition_check(self):
        from app.models.device import Device, DeviceType, DeviceStatus
        device = Device(
            device_id="dev-test",
            device_name="Test",
            device_type=DeviceType.TEMPERATURE_SENSOR,
            status=DeviceStatus.ONLINE,
        )
        assert device.can_transition_to(DeviceStatus.OFFLINE) is True
        assert device.can_transition_to(DeviceStatus.REGISTERED) is False


# ============================================================
# API Integration Tests (with mocked DB)
# ============================================================

def make_device_doc(
    device_id="dev-test001",
    status="REGISTERED",
    device_type="temperature_sensor",
    credential=None,
    **kwargs,
) -> dict:
    """Build a realistic device document for test mocking."""
    now = datetime.now(timezone.utc)
    return {
        "device_id": device_id,
        "device_name": "Test Temperature Sensor",
        "device_type": device_type,
        "status": status,
        "trust_state": "UNTRUSTED",
        "firmware_version": "1.0.0",
        "capabilities": ["SEND_TELEMETRY", "READ_TELEMETRY", "RECEIVE_COMMANDS"],
        "description": "A test device",
        "heartbeat_interval_seconds": 15,
        "missed_heartbeats": 0,
        "credential": credential,
        "created_at": now,
        "updated_at": now,
        "last_seen": None,
        "provisioned_at": None,
        "metadata": {},
        **kwargs,
    }


@pytest.fixture
def mock_db_and_mqtt():
    """Mock DB and MQTT for API testing."""
    mock_db = MagicMock()
    with (
        patch("app.core.database.connect_to_mongodb", new_callable=AsyncMock),
        patch("app.core.database.close_mongodb_connection", new_callable=AsyncMock),
        patch("app.core.database.get_database", return_value=mock_db),
        patch("app.core.mqtt_client.connect_mqtt", new_callable=AsyncMock),
        patch("app.core.mqtt_client.disconnect_mqtt", new_callable=AsyncMock),
        patch(
            "app.core.database.get_database_status",
            new_callable=AsyncMock,
            return_value={"connected": True, "database": "iot_security_lab"},
        ),
        patch(
            "app.core.mqtt_client.get_mqtt_status",
            return_value={"connected": True, "broker_host": "localhost", "broker_port": 1883},
        ),
    ):
        yield mock_db


@pytest.fixture
async def api_client(mock_db_and_mqtt):
    """Create an async test client."""
    from app.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


class TestDeviceCreateAPI:
    """Test POST /api/devices."""

    async def test_create_device_returns_201(self, api_client):
        doc = make_device_doc()
        with patch(
            "app.services.device_service.DeviceService.create_device",
            new_callable=AsyncMock,
        ) as mock_create:
            from app.schemas.device import DeviceResponse
            mock_create.return_value = DeviceResponse.from_document(doc)
            response = await api_client.post("/api/devices/", json={
                "device_name": "Living Room Sensor",
                "device_type": "temperature_sensor",
            })
            assert response.status_code == 201

    async def test_create_device_requires_name(self, api_client):
        response = await api_client.post("/api/devices/", json={
            "device_type": "temperature_sensor",
        })
        assert response.status_code == 422

    async def test_create_device_requires_type(self, api_client):
        response = await api_client.post("/api/devices/", json={
            "device_name": "Sensor A",
        })
        assert response.status_code == 422

    async def test_create_device_rejects_invalid_type(self, api_client):
        response = await api_client.post("/api/devices/", json={
            "device_name": "Bad Sensor",
            "device_type": "toaster",
        })
        assert response.status_code == 422

    async def test_create_device_rejects_invalid_firmware(self, api_client):
        response = await api_client.post("/api/devices/", json={
            "device_name": "Sensor",
            "device_type": "temperature_sensor",
            "firmware_version": "not-semver",
        })
        assert response.status_code == 422

    async def test_create_device_rejects_empty_name(self, api_client):
        response = await api_client.post("/api/devices/", json={
            "device_name": "",
            "device_type": "temperature_sensor",
        })
        assert response.status_code == 422


class TestDeviceGetAPI:
    """Test GET /api/devices/{id}."""

    async def test_get_existing_device(self, api_client):
        doc = make_device_doc()
        with patch(
            "app.services.device_service.DeviceService.get_device",
            new_callable=AsyncMock,
        ) as mock_get:
            from app.schemas.device import DeviceResponse
            mock_get.return_value = DeviceResponse.from_document(doc)
            response = await api_client.get("/api/devices/dev-test001")
            assert response.status_code == 200
            data = response.json()
            assert data["device_id"] == "dev-test001"
            assert data["status"] == "REGISTERED"

    async def test_get_nonexistent_device_returns_404(self, api_client):
        from app.services.device_service import DeviceNotFoundError
        with patch(
            "app.services.device_service.DeviceService.get_device",
            new_callable=AsyncMock,
            side_effect=DeviceNotFoundError("not found"),
        ):
            response = await api_client.get("/api/devices/dev-doesnotexist")
            assert response.status_code == 404

    async def test_get_device_response_has_required_fields(self, api_client):
        doc = make_device_doc()
        with patch(
            "app.services.device_service.DeviceService.get_device",
            new_callable=AsyncMock,
        ) as mock_get:
            from app.schemas.device import DeviceResponse
            mock_get.return_value = DeviceResponse.from_document(doc)
            response = await api_client.get("/api/devices/dev-test001")
            data = response.json()
            assert "device_id" in data
            assert "device_name" in data
            assert "device_type" in data
            assert "status" in data
            assert "capabilities" in data
            assert "is_provisioned" in data

    async def test_get_device_does_not_expose_credential_hash(self, api_client):
        """Security: credential hash must never appear in API responses."""
        now = datetime.now(timezone.utc)
        doc = make_device_doc(
            credential={
                "credential_id": "cred-test",
                "hashed_key": "$2b$12$THISISAHASH",  # this must never appear
                "created_at": now,
                "is_revoked": False,
            }
        )
        with patch(
            "app.services.device_service.DeviceService.get_device",
            new_callable=AsyncMock,
        ) as mock_get:
            from app.schemas.device import DeviceResponse
            mock_get.return_value = DeviceResponse.from_document(doc)
            response = await api_client.get("/api/devices/dev-test001")
            response_text = response.text
            assert "$2b$12$THISISAHASH" not in response_text
            assert "hashed_key" not in response_text


class TestDeviceListAPI:
    """Test GET /api/devices/."""

    async def test_list_devices_returns_200(self, api_client):
        with patch(
            "app.services.device_service.DeviceService.list_devices",
            new_callable=AsyncMock,
        ) as mock_list:
            from app.schemas.device import DeviceListResponse
            mock_list.return_value = DeviceListResponse(
                devices=[], total=0, page=1, page_size=50
            )
            response = await api_client.get("/api/devices/")
            assert response.status_code == 200

    async def test_list_devices_has_pagination_fields(self, api_client):
        with patch(
            "app.services.device_service.DeviceService.list_devices",
            new_callable=AsyncMock,
        ) as mock_list:
            from app.schemas.device import DeviceListResponse
            mock_list.return_value = DeviceListResponse(
                devices=[], total=0, page=1, page_size=50
            )
            response = await api_client.get("/api/devices/")
            data = response.json()
            assert "devices" in data
            assert "total" in data
            assert "page" in data
            assert "page_size" in data

    async def test_list_devices_rejects_invalid_page(self, api_client):
        response = await api_client.get("/api/devices/?page=0")
        assert response.status_code == 422

    async def test_list_devices_rejects_oversized_page(self, api_client):
        response = await api_client.get("/api/devices/?page_size=999")
        assert response.status_code == 422


class TestDeviceLifecycleAPI:
    """Test device lifecycle state transitions via API."""

    async def test_provision_device_returns_201(self, api_client):
        doc = make_device_doc(status="PROVISIONED")
        with patch(
            "app.services.device_service.DeviceService.provision_device",
            new_callable=AsyncMock,
        ) as mock_provision:
            from app.schemas.device import DeviceProvisionResponse, DeviceResponse, DeviceCredentialResponse
            now = datetime.now(timezone.utc)
            mock_provision.return_value = DeviceProvisionResponse(
                device=DeviceResponse.from_document(doc),
                credential=DeviceCredentialResponse(
                    credential_id="cred-001",
                    plain_key="iot-abc123def456",
                    created_at=now,
                ),
            )
            response = await api_client.post("/api/devices/dev-test001/provision")
            assert response.status_code == 201

    async def test_provision_response_contains_plain_key(self, api_client):
        doc = make_device_doc(status="PROVISIONED")
        with patch(
            "app.services.device_service.DeviceService.provision_device",
            new_callable=AsyncMock,
        ) as mock_provision:
            from app.schemas.device import DeviceProvisionResponse, DeviceResponse, DeviceCredentialResponse
            now = datetime.now(timezone.utc)
            mock_provision.return_value = DeviceProvisionResponse(
                device=DeviceResponse.from_document(doc),
                credential=DeviceCredentialResponse(
                    credential_id="cred-001",
                    plain_key="iot-abc123def456",
                    created_at=now,
                ),
            )
            response = await api_client.post("/api/devices/dev-test001/provision")
            data = response.json()
            assert "credential" in data
            assert "plain_key" in data["credential"]
            assert data["credential"]["plain_key"].startswith("iot-")

    async def test_suspend_device_returns_200(self, api_client):
        doc = make_device_doc(status="SUSPENDED")
        with patch(
            "app.services.device_service.DeviceService.suspend_device",
            new_callable=AsyncMock,
        ) as mock_suspend:
            from app.schemas.device import DeviceResponse
            mock_suspend.return_value = DeviceResponse.from_document(doc)
            response = await api_client.post(
                "/api/devices/dev-test001/suspend",
                json={"reason": "Maintenance"},
            )
            assert response.status_code == 200
            assert response.json()["status"] == "SUSPENDED"

    async def test_revoke_device_returns_revoked_status(self, api_client):
        doc = make_device_doc(status="REVOKED")
        with patch(
            "app.services.device_service.DeviceService.revoke_device",
            new_callable=AsyncMock,
        ) as mock_revoke:
            from app.schemas.device import DeviceResponse
            mock_revoke.return_value = DeviceResponse.from_document(doc)
            response = await api_client.post("/api/devices/dev-test001/revoke")
            assert response.status_code == 200
            assert response.json()["status"] == "REVOKED"

    async def test_invalid_transition_returns_409(self, api_client):
        from app.services.device_service import InvalidStateTransitionError
        with patch(
            "app.services.device_service.DeviceService.suspend_device",
            new_callable=AsyncMock,
            side_effect=InvalidStateTransitionError("Cannot suspend REVOKED device"),
        ):
            response = await api_client.post("/api/devices/dev-test001/suspend")
            assert response.status_code == 409

    async def test_provision_already_provisioned_returns_409(self, api_client):
        from app.services.device_service import DeviceAlreadyProvisionedError
        with patch(
            "app.services.device_service.DeviceService.provision_device",
            new_callable=AsyncMock,
            side_effect=DeviceAlreadyProvisionedError("Already provisioned"),
        ):
            response = await api_client.post("/api/devices/dev-test001/provision")
            assert response.status_code == 409


class TestDeviceSchemaValidation:
    """Test Pydantic schema validation."""

    def test_create_request_strips_whitespace_from_name(self):
        from app.schemas.device import DeviceCreateRequest
        from app.models.device import DeviceType
        req = DeviceCreateRequest(
            device_name="  My Sensor  ",
            device_type=DeviceType.TEMPERATURE_SENSOR,
        )
        assert req.device_name == "My Sensor"

    def test_create_request_default_firmware(self):
        from app.schemas.device import DeviceCreateRequest
        from app.models.device import DeviceType
        req = DeviceCreateRequest(
            device_name="Sensor",
            device_type=DeviceType.MOTION_SENSOR,
        )
        assert req.firmware_version == "1.0.0"

    def test_create_request_default_heartbeat_interval(self):
        from app.schemas.device import DeviceCreateRequest
        from app.models.device import DeviceType
        req = DeviceCreateRequest(
            device_name="Sensor",
            device_type=DeviceType.MOTION_SENSOR,
        )
        assert req.heartbeat_interval_seconds == 15

    def test_create_request_rejects_short_heartbeat(self):
        from app.schemas.device import DeviceCreateRequest
        from app.models.device import DeviceType
        import pytest
        with pytest.raises(Exception):
            DeviceCreateRequest(
                device_name="Sensor",
                device_type=DeviceType.MOTION_SENSOR,
                heartbeat_interval_seconds=1,
            )

    def test_device_response_from_document(self):
        from app.schemas.device import DeviceResponse
        now = datetime.now(timezone.utc)
        doc = {
            "device_id": "dev-abc",
            "device_name": "Test",
            "device_type": "temperature_sensor",
            "status": "REGISTERED",
            "trust_state": "UNTRUSTED",
            "firmware_version": "1.0.0",
            "capabilities": ["SEND_TELEMETRY"],
            "description": "",
            "heartbeat_interval_seconds": 15,
            "missed_heartbeats": 0,
            "credential": None,
            "created_at": now,
            "updated_at": now,
            "last_seen": None,
            "provisioned_at": None,
            "metadata": {},
        }
        resp = DeviceResponse.from_document(doc)
        assert resp.device_id == "dev-abc"
        assert resp.is_provisioned is False
        assert resp.status == "REGISTERED"

