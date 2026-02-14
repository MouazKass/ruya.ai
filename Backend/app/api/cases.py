from __future__ import annotations

from fastapi import APIRouter, Query, Request

from app.models import CaseDetailResponse


router = APIRouter(prefix="/api", tags=["cases"])


@router.get("/case/{case_id}", response_model=CaseDetailResponse)
async def get_case(
    case_id: str,
    request: Request,
    run_id: str | None = Query(default=None),
) -> CaseDetailResponse:
    return await request.app.state.service.get_case_details(case_id=case_id, run_id=run_id)
