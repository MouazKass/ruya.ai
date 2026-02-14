from __future__ import annotations

import logging
from typing import Any


LOGGER = logging.getLogger(__name__)


class EmailStubProvider:
    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run

    async def send_email(self, payload: dict[str, Any]) -> dict[str, Any]:
        LOGGER.info("Email stub invoked for case %s", payload.get("case_id"))
        return {
            "provider": "email_stub",
            "dry_run": self.dry_run,
            "status": "queued",
            "summary": f"Verification email prepared for case {payload.get('case_id')}",
        }
