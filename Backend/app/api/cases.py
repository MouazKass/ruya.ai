from __future__ import annotations

from fastapi import APIRouter, Request

from app.models import CaseDetailResponse


router = APIRouter(prefix="/api", tags=["cases"])


@router.get("/case/{case_id}", response_model=CaseDetailResponse)
async def get_case(case_id: str, request: Request) -> CaseDetailResponse:
    return await request.app.state.service.get_case_details(case_id=case_id)
