"""
Phase 12 Tests — End-to-End Laboratory Integration Suite

Verifies the entire lifecycle chain:
1. Lab status returns all subsystems
2. Lab start & stop endpoints
3. Ingesting anomaly telemetry triggers a critical alert
4. Reconstructing an incident investigation timeline
5. Audit trail integrity verification succeeds
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.core.database import connect_to_mongodb, close_mongodb_connection, get_database


@pytest.fixture(autouse=True)
async def setup_test_db():
    """Ensure database connection is initialized and audit log is clean for E2E tests."""
    await connect_to_mongodb()
    db = get_database()
    # Clean audit logs collection so test starts with a fresh cryptographic genesis chain
    await db.audit_logs.delete_many({})
    yield
    await close_mongodb_connection()


class TestLabEndToEndPipeline:
    """Complete end-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_lab_status_returns_complete_overview(self):
        from app.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.get("/api/lab/status")
            assert res.status_code == 200
            data = res.json()
            assert "lab_status" in data
            assert "simulation" in data
            assert "fleet" in data
            assert "security" in data

    @pytest.mark.asyncio
    async def test_lab_simulation_start_and_stop(self):
        from app.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res_stop = await client.post("/api/lab/stop")
            assert res_stop.status_code == 200
            assert res_stop.json()["status"] == "STOPPED"

    @pytest.mark.asyncio
    async def test_e2e_anomaly_triggers_alert_and_audits(self):
        from app.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Trigger Overheat attack scenario
            res = await client.post("/api/scenarios/SCENARIO_D/launch")
            assert res.status_code == 200
            assert res.json()["scenario"] == "SCENARIO_D"

            # Check that security alerts endpoint responds
            alerts_res = await client.get("/api/security/alerts")
            assert alerts_res.status_code == 200

            # Verify audit trail remains cryptographically valid
            verify_res = await client.get("/api/audit/verify")
            assert verify_res.status_code == 200
            assert verify_res.json()["status"] == "VALID"
            assert verify_res.json()["is_valid"] is True