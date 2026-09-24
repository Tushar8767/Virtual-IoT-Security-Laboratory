"""
Phase 2 Tests — Device Simulator Framework

Tests:
1. VirtualTemperatureSensor value generation and bounds
2. VirtualMotionSensor value generation and triggers
3. VirtualSmartActuator value generation and states
4. Telemetry payload schema compliance
5. Heartbeat payload schema compliance
6. SimulatorManager concurrent startup and shutdown
"""

import pytest
import asyncio
from device_simulator.devices.sensors import (
    VirtualTemperatureSensor,
    VirtualMotionSensor,
    VirtualSmartActuator,
)
from device_simulator.simulator_manager import SimulatorManager


class TestSensorValueGeneration:
    """Test sensor value realism and schemas."""

    def test_temperature_sensor_normal_range(self):
        sensor = VirtualTemperatureSensor(device_id="TEST-TEMP")
        values = sensor.generate_sensor_values()
        assert "temperature_c" in values
        assert "temperature_f" in values
        assert 20.0 <= values["temperature_c"] <= 28.0
        assert values["unit"] == "Celsius"
        assert values["sensor_health"] == "OPTIMAL"

    def test_temperature_sensor_abnormal_anomaly(self):
        sensor = VirtualTemperatureSensor(device_id="TEST-TEMP")
        sensor.mode = "abnormal"
        values = sensor.generate_sensor_values()
        assert values["temperature_c"] >= 70.0
        assert values["sensor_health"] == "OVERHEATING"

    def test_motion_sensor_trigger(self):
        sensor = VirtualMotionSensor(device_id="TEST-MOTION")
        values = sensor.generate_sensor_values()
        assert "motion_detected" in values
        assert isinstance(values["motion_detected"], bool)
        assert "ambient_light_lux" in values

    def test_actuator_state(self):
        actuator = VirtualSmartActuator(device_id="TEST-ACT")
        values = actuator.generate_sensor_values()
        assert values["actuator_state"] == "ON"
        assert values["power_consumption_watts"] > 0.0


class TestPayloadFormatting:
    """Test telemetry and heartbeat payload schema compliance."""

    def test_telemetry_payload_schema(self):
        sensor = VirtualTemperatureSensor(device_id="PY-TEMP-001")
        payload = sensor.build_telemetry_payload()
        assert payload["device_id"] == "PY-TEMP-001"
        assert payload["event_id"].startswith("tel-")
        assert payload["sequence_number"] == 1
        assert "values" in payload
        assert "timestamp" in payload
        assert "correlation_id" in payload

    def test_sequence_number_increments(self):
        sensor = VirtualTemperatureSensor(device_id="PY-TEMP-001")
        p1 = sensor.build_telemetry_payload()
        p2 = sensor.build_telemetry_payload()
        assert p1["sequence_number"] == 1
        assert p2["sequence_number"] == 2

    def test_heartbeat_payload_schema(self):
        sensor = VirtualTemperatureSensor(device_id="PY-TEMP-001")
        hb = sensor.build_heartbeat_payload()
        assert hb["device_id"] == "PY-TEMP-001"
        assert hb["event_id"].startswith("hb-")
        assert hb["status"] == "ONLINE"


class TestSimulatorManager:
    """Test concurrent fleet execution."""

    @pytest.mark.asyncio
    async def test_multi_device_concurrency(self):
        emitted_telemetry = []

        def on_tel(data):
            emitted_telemetry.append(data)

        mgr = SimulatorManager()
        mgr.create_device_from_dict(
            {"device_id": "SIM-1", "device_type": "temperature_sensor", "telemetry_interval_seconds": 1},
            on_telemetry_emit=on_tel,
        )
        mgr.create_device_from_dict(
            {"device_id": "SIM-2", "device_type": "motion_sensor", "telemetry_interval_seconds": 1},
            on_telemetry_emit=on_tel,
        )

        assert mgr.total_devices_count == 2
        await mgr.start_all()
        assert mgr.active_devices_count == 2

        # Allow devices to emit at least 1 cycle
        await asyncio.sleep(1.2)

        await mgr.stop_all()
        assert mgr.active_devices_count == 0
        assert len(emitted_telemetry) >= 2