"""
Scenarios API Router — Controlled Attack Simulation

Endpoints:
    GET  /api/scenarios/                     — list all 7 attack scenarios
    GET  /api/scenarios/{scenario_id}        — get scenario details
    POST /api/scenarios/{scenario_id}/launch — trigger an attack scenario
"""

from fastapi import APIRouter, HTTPException, status
from attack_simulator.scenarios.definitions import get_scenario_list, get_scenario_by_id
from attack_simulator.engine.runner import ScenarioRunner
from app.models.audit import AuditAction, AuditResult, AuditRepository, get_audit_repository
from fastapi import Depends

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.get("/", summary="List all security attack scenarios")
async def list_scenarios():
    """Retrieve catalog of all 7 controlled attack scenarios."""
    scenarios = get_scenario_list()
    return {"count": len(scenarios), "scenarios": scenarios}


@router.get("/{scenario_id}", summary="Get scenario details")
async def get_scenario(scenario_id: str):
    """Retrieve details, description, and expected detection for a specific scenario."""
    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario_id}' not found",
        )
    return scenario


@router.post("/{scenario_id}/launch", summary="Launch a controlled attack scenario")
async def launch_scenario(
    scenario_id: str,
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    """
    Execute a controlled attack scenario within the lab.
    Logs scenario execution into the audit trail.
    """
    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario_id}' not found",
        )

    await audit_repo.log(
        action=AuditAction.SCENARIO_STARTED,
        target=scenario_id,
        result=AuditResult.SUCCESS,
        actor="operator",
        metadata={"scenario_name": scenario["name"]},
    )

    runner = ScenarioRunner()
    result = await runner.execute_scenario(scenario_id)

    await audit_repo.log(
        action=AuditAction.SCENARIO_COMPLETED,
        target=scenario_id,
        result=AuditResult.SUCCESS if result.get("detected") else AuditResult.FAILURE,
        actor="operator",
        metadata={"run_id": result.get("run_id"), "detected": result.get("detected")},
    )

    return result