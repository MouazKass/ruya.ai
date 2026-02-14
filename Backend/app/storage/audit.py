from __future__ import annotations

import json
from typing import Any

from app.storage.clickhouse import ClickHouseClient


def log_audit_event(
    clickhouse: ClickHouseClient,
    event_type: str,
    actor: str,
    payload: dict[str, Any],
    run_id: str | None = None,
    case_id: str | None = None,
) -> None:
    clickhouse.insert(
        table="audit_logs",
        rows=[
            [
                run_id,
                case_id,
                event_type,
                actor,
                json.dumps(payload, default=str),
            ]
        ],
        column_names=["run_id", "case_id", "event_type", "actor", "payload_json"],
    )
