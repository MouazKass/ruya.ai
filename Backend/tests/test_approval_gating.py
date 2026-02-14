from __future__ import annotations

import pytest

from app.dispatch.base import DispatchManager


class VoiceSpy:
    def __init__(self) -> None:
        self.calls = 0

    async def send_briefing(self, payload: dict) -> dict:
        self.calls += 1
        return {"ok": True, "payload": payload}


class EmailSpy:
    def __init__(self) -> None:
        self.calls = 0

    async def send_email(self, payload: dict) -> dict:
        self.calls += 1
        return {"ok": True, "payload": payload}


@pytest.mark.asyncio
async def test_dispatch_is_blocked_without_approval() -> None:
    voice = VoiceSpy()
    email = EmailSpy()
    manager = DispatchManager(voice_provider=voice, email_provider=email, dry_run=True)

    result = await manager.dispatch_if_approved(
        case_id="CASE-001",
        decision_payload={"severity": 8.2, "confidence": 73.0},
        approval_status="rejected",
        notes="rejecting",
    )

    assert result["dispatched"] is False
    assert voice.calls == 0
    assert email.calls == 0
