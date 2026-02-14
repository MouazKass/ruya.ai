from __future__ import annotations

from fastapi import APIRouter, Request

from app.models import ApprovalRequest, ApprovalResponse


router = APIRouter(prefix="/api", tags=["approvals"])


@router.post("/approval/{case_id}", response_model=ApprovalResponse)
async def apply_approval(case_id: str, payload: ApprovalRequest, request: Request) -> ApprovalResponse:
    return await request.app.state.service.apply_approval(case_id=case_id, approval=payload)
