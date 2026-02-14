from __future__ import annotations

import logging
from typing import Any, Protocol

from app.models import ApprovalStatus


LOGGER = logging.getLogger(__name__)


class VoiceProvider(Protocol):
    async def send_briefing(self, payload: dict[str, Any]) -> dict[str, Any]:
        ...


class EmailProvider(Protocol):
    async def send_email(self, payload: dict[str, Any]) -> dict[str, Any]:
        ...


class DispatchManager:
    def __init__(self, voice_provider: VoiceProvider, email_provider: EmailProvider, dry_run: bool = True) -> None:
        self.voice_provider = voice_provider
        self.email_provider = email_provider
        self.dry_run = dry_run

    async def dispatch_if_approved(
        self,
        case_id: str,
        decision_payload: dict[str, Any],
        approval_status: str,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if approval_status != ApprovalStatus.approved.value:
            LOGGER.info("Dispatch skipped for case %s: approval status is %s", case_id, approval_status)
            return {"dispatched": False, "reason": "approval_required"}

        message = {
            "case_id": case_id,
            "severity": decision_payload.get("severity"),
            "confidence": decision_payload.get("confidence"),
            "rationale": decision_payload.get("rationale"),
            "notes": notes,
            "dry_run": self.dry_run,
        }
        voice_result = await self.voice_provider.send_briefing(message)
        email_result = await self.email_provider.send_email(message)
        return {
            "dispatched": True,
            "dry_run": self.dry_run,
            "voice": voice_result,
            "email": email_result,
        }
