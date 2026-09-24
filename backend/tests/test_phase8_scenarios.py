"""
Phase 8 Tests — Attack Scenario Simulation

Tests:
1. Scenario definitions catalog (all 7 scenarios present)
2. REST API: GET /api/scenarios/
3. REST API: GET /api/scenarios/{id}
4. Rejection of unknown scenario IDs (404)
5. REST API: POST /api/scenarios/{id}/launch
6. Audit logging of SCENARIO_STARTED and SCENARIO_COMPLETED
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from attack_simulator.scenarios.definitions import get_scenario_list, get_scenario_by_id
from app.models.audit import get_audit_repository


class TestScenarioDefinitions:
    """Test scenario catalog."""

    def test_all_seven_scenarios_exist(self):
        scenarios = get_scenario_list()
        assert len(scenarios) == 7
        ids = [s["id"] for s in scenarios]
        assert "SCENARIO_A" in ids
        assert "SCENARIO_B" in ids
        assert "SCENARIO_C" in ids
        assert "SCENARIO_D" in ids
        assert "SCENARIO_E" in ids
        assert "SCENARIO_F" in ids
        assert "SCENARIO_G" in ids

    def test_scenario_d_targets_proteus_device(self):
        scenario = get_scenario_by_id("SCENARIO_D")
        assert scenario is not None
        assert scenario["target_device"] == "LPC2138-TEMP-001"
        assert scenario["severity"] == "CRITICAL"


class TestScenarioAPI:
    """Test scenario REST endpoints."""

    @pytest.mark.asyncio
    async def test_list_scenarios_endpoint(self):
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            res = await client.get("/api/scenarios/")
            assert res.status_code == 200
            data = res.json()
            assert data["count"] == 7
            assert len(data["scenarios"]) == 7

    @pytest.mark.asyncio
    async def test_get_scenario_details(self):
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            res = await client.get("/api/scenarios/SCENARIO_A")
            assert res.status_code == 200
            data = res.json()
            assert data["name"] == "Rogue Device Injection"

    @pytest.mark.asyncio
    async def test_get_nonexistent_scenario_returns_404(self):
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            res = await client.get("/api/scenarios/SCENARIO_Z")
            assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_launch_scenario_endpoint(self):
        from app.main import app

        mock_audit = MagicMock()
        mock_audit.log = AsyncMock()
        app.dependency_overrides[get_audit_repository] = lambda: mock_audit

        # Mock ScenarioRunner.execute_scenario so it doesn't open real network sockets in unit test
        with patch(
            "attack_simulator.engine.runner.ScenarioRunner.execute_scenario",
            new_callable=AsyncMock,
            return_value={"run_id": "run-test", "scenario": "SCENARIO_A", "status": "COMPLETED", "detected": True},
        ):
            try:
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    res = await client.post("/api/scenarios/SCENARIO_A/launch")
                    assert res.status_code == 200
                    data = res.json()
                    assert data["scenario"] == "SCENARIO_A"
                    assert data["status"] == "COMPLETED"

                    # Verify audit logging was called
                    assert mock_audit.log.await_count == 2
            finally:
                app.dependency_overrides.clear()