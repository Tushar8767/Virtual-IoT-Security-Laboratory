"""
Phase 3 Tests — Secure IoT Gateway & Communication Layer

Tests:
1. Topic format validation
2. JSON payload parsing and rejection of malformed data
3. Device impersonation detection (topic mismatch)
4. Unknown device rejection against device registry
5. Revoked / Suspended device rejection
6. Proteus UART bridge parsing for LPC2138
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from app.telemetry.gateway import SecureIotGateway
from app.models.device import DeviceStatus
from device_simulator.protocols.uart_bridge import ProteusUartBridge


@pytest.fixture
def mock_device_repo():
    repo = MagicMock()
    return repo


class TestSecureIotGateway:
    """Test gateway security boundary checks."""

    @pytest.mark.asyncio
    async def test_rejects_invalid_topic_format(self, mock_device_repo):
        gateway = SecureIotGateway(mock_device_repo)
        res, payload = await gateway.validate_inbound_message(
            topic="invalid/topic",
            raw_payload=b'{"device_id": "D1"}',
        )
        assert res.is_valid is False
        assert res.reason == "INVALID_TOPIC_FORMAT"

    @pytest.mark.asyncio
    async def test_rejects_malformed_json(self, mock_device_repo):
        gateway = SecureIotGateway(mock_device_repo)
        res, payload = await gateway.validate_inbound_message(
            topic="lab/devices/D1/telemetry",
            raw_payload=b"NOT_A_JSON_STRING",
        )
        assert res.is_valid is False
        assert res.reason == "MALFORMED_JSON_PAYLOAD"

    @pytest.mark.asyncio
    async def test_detects_device_impersonation(self, mock_device_repo):
        """Scenario F: A device claiming to be D2 publishes on D1's topic."""
        gateway = SecureIotGateway(mock_device_repo)
        raw = json.dumps({"device_id": "IMPOSTOR-001", "temperature": 25.0}).encode()
        res, payload = await gateway.validate_inbound_message(
            topic="lab/devices/LEGIT-001/telemetry",
            raw_payload=raw,
        )
        assert res.is_valid is False
        assert "DEVICE_IMPERSONATION" in res.reason

    @pytest.mark.asyncio
    async def test_rejects_unknown_device(self, mock_device_repo):
        """Scenario A: Device not registered in database."""
        mock_device_repo.find_by_id = AsyncMock(return_value=None)
        gateway = SecureIotGateway(mock_device_repo)
        raw = json.dumps({"device_id": "UNKNOWN-001"}).encode()
        res, payload = await gateway.validate_inbound_message(
            topic="lab/devices/UNKNOWN-001/telemetry",
            raw_payload=raw,
        )
        assert res.is_valid is False
        assert "UNKNOWN_DEVICE" in res.reason

    @pytest.mark.asyncio
    async def test_rejects_revoked_device(self, mock_device_repo):
        mock_device_repo.find_by_id = AsyncMock(return_value={
            "device_id": "REVOKED-001",
            "status": DeviceStatus.REVOKED.value,
        })
        gateway = SecureIotGateway(mock_device_repo)
        raw = json.dumps({"device_id": "REVOKED-001"}).encode()
        res, payload = await gateway.validate_inbound_message(
            topic="lab/devices/REVOKED-001/telemetry",
            raw_payload=raw,
        )
        assert res.is_valid is False
        assert "DEVICE_REVOKED" in res.reason

    @pytest.mark.asyncio
    async def test_accepts_valid_provisioned_device(self, mock_device_repo):
        mock_device_repo.find_by_id = AsyncMock(return_value={
            "device_id": "PY-TEMP-001",
            "status": DeviceStatus.PROVISIONED.value,
        })
        gateway = SecureIotGateway(mock_device_repo)
        raw = json.dumps({"device_id": "PY-TEMP-001", "temp": 24.5}).encode()
        res, payload = await gateway.validate_inbound_message(
            topic="lab/devices/PY-TEMP-001/telemetry",
            raw_payload=raw,
        )
        assert res.is_valid is True
        assert res.reason == "OK"
        assert payload["temp"] == 24.5


class TestProteusUartBridge:
    """Test serial parser for LPC2138 LM35 node."""

    def test_parses_formatted_temperature_string(self):
        bridge = ProteusUartBridge(device_id="LPC2138-TEMP-001")
        payload = bridge.parse_raw_line("TEMP: 28.5 C")
        assert payload is not None
        assert payload["device_id"] == "LPC2138-TEMP-001"
        assert payload["values"]["temperature_c"] == 28.5
        assert payload["values"]["temperature_f"] == 83.3
        assert payload["values"]["source"] == "proteus_lpc2138_uart0"

    def test_parses_json_string(self):
        bridge = ProteusUartBridge(device_id="LPC2138-TEMP-001")
        payload = bridge.parse_raw_line('{"temp": 24.0}')
        assert payload is not None
        assert payload["values"]["temperature_c"] == 24.0

    def test_ignores_empty_or_garbage_lines(self):
        bridge = ProteusUartBridge(device_id="LPC2138-TEMP-001")
        assert bridge.parse_raw_line("") is None
        assert bridge.parse_raw_line("   \n") is None