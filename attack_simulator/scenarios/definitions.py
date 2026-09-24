"""
Attack Scenario Definitions — Controlled Security Simulations

All attack simulations are contained entirely within the virtual lab.
They test whether the Gateway, Authentication layer, and Security Engine
detect, block, and alert on malicious actions as expected.
"""

from typing import Dict, Any, List


SCENARIOS: Dict[str, Dict[str, Any]] = {
    "SCENARIO_A": {
        "id": "SCENARIO_A",
        "name": "Rogue Device Injection",
        "category": "Identity Violation",
        "description": "An unregistered rogue device (ROGUE-999) attempts to inject telemetry into the laboratory.",
        "target_device": "ROGUE-999",
        "expected_detection": "UNKNOWN_DEVICE",
        "severity": "HIGH",
    },
    "SCENARIO_B": {
        "id": "SCENARIO_B",
        "name": "Credential Brute Force / Auth Flood",
        "category": "Authentication Attack",
        "description": "Rapid succession of invalid API keys sent against a provisioned device.",
        "target_device": "PY-TEMP-001",
        "expected_detection": "AUTH_FAILURE_FLOOD",
        "severity": "HIGH",
    },
    "SCENARIO_C": {
        "id": "SCENARIO_C",
        "name": "Telemetry Flooding / Denial of Service",
        "category": "Availability Attack",
        "description": "Burst of high-frequency telemetry packets exceeding provisioned rate limits.",
        "target_device": "PY-TEMP-001",
        "expected_detection": "TELEMETRY_RATE_ANOMALY",
        "severity": "MEDIUM",
    },
    "SCENARIO_D": {
        "id": "SCENARIO_D",
        "name": "Sensor Value Tampering / Overheating Anomaly",
        "category": "Integrity Attack",
        "description": "Manipulating sensor readings to 105.0°C to simulate physical overheating / false sensor injection.",
        "target_device": "LPC2138-TEMP-001",
        "expected_detection": "VALUE_OUT_OF_BOUNDS",
        "severity": "CRITICAL",
    },
    "SCENARIO_E": {
        "id": "SCENARIO_E",
        "name": "Heartbeat Starvation / Silent Node",
        "category": "Availability Attack",
        "description": "Abruptly halting heartbeats from an active node to trigger timeout alerts.",
        "target_device": "PY-MOTION-001",
        "expected_detection": "HEARTBEAT_TIMEOUT",
        "severity": "MEDIUM",
    },
    "SCENARIO_F": {
        "id": "SCENARIO_F",
        "name": "Device Identity Impersonation",
        "category": "Identity Attack",
        "description": "Transmitting a payload claiming to be PY-ACTUATOR-001 on PY-TEMP-001's communication channel.",
        "target_device": "PY-ACTUATOR-001",
        "expected_detection": "DEVICE_IMPERSONATION",
        "severity": "CRITICAL",
    },
    "SCENARIO_G": {
        "id": "SCENARIO_G",
        "name": "Unauthorized Actuator Command",
        "category": "Authorization Attack",
        "description": "A temperature sensor lacking control capabilities attempts to issue actuator commands.",
        "target_device": "PY-TEMP-001",
        "expected_detection": "AUTHZ_FAILURE",
        "severity": "HIGH",
    },
}


def get_scenario_list() -> List[Dict[str, Any]]:
    return list(SCENARIOS.values())


def get_scenario_by_id(scenario_id: str) -> Dict[str, Any]:
    return SCENARIOS.get(scenario_id.upper())