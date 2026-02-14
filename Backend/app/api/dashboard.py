from __future__ import annotations

from fastapi import APIRouter, Request

from app.models import DashboardResponse


router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(request: Request) -> DashboardResponse:
    return await request.app.state.service.get_dashboard()
