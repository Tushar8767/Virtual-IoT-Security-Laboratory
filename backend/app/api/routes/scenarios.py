"""
Scenarios API Router — Phase 0 Skeleton
Full implementation in Phase 8.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.get("/", summary="List scenarios [Phase 8]")
async def list_scenarios():
    return {"scenarios": [], "message": "Attack scenarios implemented in Phase 8"}

