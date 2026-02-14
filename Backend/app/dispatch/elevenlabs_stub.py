from __future__ import annotations

import logging
from typing import Any


LOGGER = logging.getLogger(__name__)


class ElevenLabsStubProvider:
    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run

    async def send_briefing(self, payload: dict[str, Any]) -> dict[str, Any]:
        LOGGER.info("ElevenLabs stub invoked for case %s", payload.get("case_id"))
        return {
            "provider": "elevenlabs_stub",
            "dry_run": self.dry_run,
            "status": "queued",
            "summary": f"Voice briefing prepared for case {payload.get('case_id')}",
        }
