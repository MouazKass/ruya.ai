from __future__ import annotations

from fastapi import APIRouter, Request

from app.models import SuggestionExecuteRequest, SuggestionExecuteResponse


router = APIRouter(prefix="/api", tags=["suggestions"])


@router.post("/suggestion/{case_id}/execute", response_model=SuggestionExecuteResponse)
async def execute_suggestion(
    case_id: str,
    payload: SuggestionExecuteRequest,
    request: Request,
) -> SuggestionExecuteResponse:
    """Execute the AI-generated suggestion for a case (the 'Do it' button)."""
    return await request.app.state.service.execute_suggestion(case_id=case_id, request=payload)
