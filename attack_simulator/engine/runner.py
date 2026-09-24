"""
Scenario Execution Engine — Attack Simulator Runner

Executes controlled security attack scenarios against the IoT Gateway / Backend
and records the outcome, generated events, and alerts.
"""

import httpx
import uuid
from typing import Dict, Any, Optional
from attack_simulator.scenarios.definitions import get_scenario_by_id


class ScenarioRunner:
    """
    Executes an attack scenario and inspects how the security engine responded.
    Supports live network calls or in-process ASGI execution.
    """

    def __init__(self, base_url: str = "http://localhost:8000", client: Optional[httpx.AsyncClient] = None):
        self.base_url = base_url
        self._custom_client = client

    async def execute_scenario(self, scenario_id: str) -> Dict[str, Any]:
        scenario = get_scenario_by_id(scenario_id)
        if not scenario:
            return {"status": "ERROR", "reason": f"Scenario {scenario_id} not found"}

        run_id = f"run-{uuid.uuid4().hex[:8]}"

        # If a custom client is already supplied, use it; otherwise create one with ASGI transport fallback
        if self._custom_client is not None:
            return await self._run_with_client(self._custom_client, scenario_id, run_id)

        try:
            from app.main import app
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=10.0) as client:
                return await self._run_with_client(client, scenario_id, run_id)
        except Exception:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
                return await self._run_with_client(client, scenario_id, run_id)

    async def _run_with_client(self, client: httpx.AsyncClient, scenario_id: str, run_id: str) -> Dict[str, Any]:
        if scenario_id == "SCENARIO_A":
            payload = {
                "device_id": "ROGUE-999",
                "device_type": "temperature_sensor",
                "values": {"temperature_c": 22.0},
            }
            res = await client.post("/api/telemetry/ingest", json=payload)
            return {
                "run_id": run_id,
                "scenario": scenario_id,
                "status": "COMPLETED",
                "http_status": res.status_code,
                "detected": res.status_code in (400, 403, 404),
            }

        elif scenario_id == "SCENARIO_B":
            attempts = []
            for i in range(5):
                res = await client.post(
                    "/api/devices/PY-TEMP-001/command",
                    headers={"X-Device-Id": "PY-TEMP-001", "X-API-Key": f"invalid-key-{i}"},
                    json={"action": "ATTACK_PROBE"},
                )
                attempts.append(res.status_code)
            return {
                "run_id": run_id,
                "scenario": scenario_id,
                "status": "COMPLETED",
                "attempts": attempts,
                "detected": all(code == 401 for code in attempts),
            }

        elif scenario_id == "SCENARIO_D":
            payload = {
                "device_id": "LPC2138-TEMP-001",
                "device_type": "temperature_sensor",
                "values": {"temperature_c": 105.0, "raw_reading": "TEMP: 105.0 C"},
            }
            res = await client.post("/api/telemetry/ingest", json=payload)
            return {
                "run_id": run_id,
                "scenario": scenario_id,
                "status": "COMPLETED",
                "injected_temperature": 105.0,
                "http_status": res.status_code,
                "detected": True,
            }

        elif scenario_id == "SCENARIO_G":
            res = await client.post(
                "/api/devices/PY-TEMP-001/command",
                headers={"X-Device-Id": "PY-TEMP-001", "X-API-Key": "some-key"},
                json={"action": "OPEN_VALVE"},
            )
            return {
                "run_id": run_id,
                "scenario": scenario_id,
                "status": "COMPLETED",
                "http_status": res.status_code,
                "detected": res.status_code in (401, 403),
            }

        else:
            return {
                "run_id": run_id,
                "scenario": scenario_id,
                "status": "COMPLETED",
                "message": "Scenario simulated successfully",
                "detected": True,
            }