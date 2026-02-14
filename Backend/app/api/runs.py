from __future__ import annotations

from fastapi import APIRouter, Request

from app.models import RunStatusResponse, StartRunRequest, StartRunResponse


router = APIRouter(prefix="/api", tags=["runs"])


@router.post("/run/start", response_model=StartRunResponse)
async def start_run(payload: StartRunRequest, request: Request) -> StartRunResponse:
    run_id = await request.app.state.service.start_run(num_cases=payload.num_cases)
    return StartRunResponse(run_id=run_id, status="running")


@router.get("/run/{run_id}/status", response_model=RunStatusResponse)
async def get_run_status(run_id: str, request: Request) -> RunStatusResponse:
    return await request.app.state.service.get_run_status(run_id=run_id)
