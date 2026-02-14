from __future__ import annotations

import pytest

from app.dispatch.base import DispatchManager
from app.models import ApprovalStatus


class VoiceFail:
    async def send_briefing(self, payload: dict) -> dict:
        raise RuntimeError("voice provider unavailable")


class EmailSpy:
    def __init__(self) -> None:
        self.calls = 0

    async def send_email(self, payload: dict) -> dict:
        self.calls += 1
        return {"ok": True}


@pytest.mark.asyncio
async def test_dispatch_captures_channel_failures_without_raising() -> None:
    email = EmailSpy()
    manager = DispatchManager(voice_provider=VoiceFail(), email_provider=email, dry_run=True)

    result = await manager.dispatch_if_approved(
        case_id="CASE-001",
        decision_payload={"severity": 8.2, "confidence": 73.0, "rationale": "test"},
        approval_status=ApprovalStatus.approved.value,
        notes="go",
    )

    assert result["dispatched"] is False
    assert result.get("partial") is True
    assert "voice" in result.get("errors", {})
    assert email.calls == 1
