from __future__ import annotations

import logging

from app.storage.clickhouse import ClickHouseClient


LOGGER = logging.getLogger(__name__)


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS cases (
        case_id String,
        run_id String,
        case_date Date,
        country String,
        city String,
        lat Float64,
        lon Float64,
        pathogen_label Nullable(String),
        normalized_json String,
        ground_truth_json String,
        embedding Array(Float32),
        created_at DateTime DEFAULT now()
    )
    ENGINE = MergeTree
    ORDER BY (case_id, run_id, created_at)
    """,
    """
    CREATE TABLE IF NOT EXISTS agent_outputs (
        output_id UUID DEFAULT generateUUIDv4(),
        run_id String,
        case_id String,
        agent_name String,
        output_json String,
        score Float64,
        confidence Float64,
        created_at DateTime DEFAULT now()
    )
    ENGINE = MergeTree
    ORDER BY (case_id, run_id, agent_name, created_at)
    """,
    """
    CREATE TABLE IF NOT EXISTS decisions (
        decision_id UUID DEFAULT generateUUIDv4(),
        run_id String,
        case_id String,
        fused_score Float64,
        severity Float64,
        confidence Float64,
        eligible_for_review UInt8,
        rationale String,
        contributions_json String,
        threshold Float64,
        suggestion String DEFAULT '',
        created_at DateTime DEFAULT now()
    )
    ENGINE = MergeTree
    ORDER BY (case_id, run_id, created_at)
    """,
    # Migration: add suggestion column to existing decisions tables
    """
    ALTER TABLE decisions ADD COLUMN IF NOT EXISTS suggestion String DEFAULT ''
    """,
    """
    CREATE TABLE IF NOT EXISTS suggestion_executions (
        execution_id UUID DEFAULT generateUUIDv4(),
        case_id String,
        run_id String,
        suggestion String,
        operator_name Nullable(String),
        notes Nullable(String),
        dispatch_json String,
        executed_at DateTime DEFAULT now()
    )
    ENGINE = MergeTree
    ORDER BY (case_id, run_id, executed_at)
    """,
    """
    CREATE TABLE IF NOT EXISTS approvals (
        approval_id UUID DEFAULT generateUUIDv4(),
        case_id String,
        run_id String,
        status String,
        reviewer_name Nullable(String),
        timestamp DateTime DEFAULT now(),
        notes String,
        dispatch_json String
    )
    ENGINE = MergeTree
    ORDER BY (case_id, run_id, timestamp)
    """,
    """
    CREATE TABLE IF NOT EXISTS runs (
        run_event_id UUID DEFAULT generateUUIDv4(),
        run_id String,
        status String,
        started_at DateTime,
        ended_at Nullable(DateTime),
        config_json String,
        error Nullable(String),
        processed UInt32,
        total UInt32,
        event_time DateTime DEFAULT now()
    )
    ENGINE = MergeTree
    ORDER BY (run_id, event_time)
    """,
    """
    CREATE TABLE IF NOT EXISTS strategy_memory (
        memory_id UUID DEFAULT generateUUIDv4(),
        run_id String,
        case_id String,
        strategy_notes String,
        updated_prompts_json String,
        weights_json String,
        threshold Float64,
        embedding Array(Float32),
        created_at DateTime DEFAULT now()
    )
    ENGINE = MergeTree
    ORDER BY (run_id, case_id, created_at)
    """,
    """
    CREATE TABLE IF NOT EXISTS audit_logs (
        event_id UUID DEFAULT generateUUIDv4(),
        run_id Nullable(String),
        case_id Nullable(String),
        event_type String,
        actor String,
        payload_json String,
        timestamp DateTime DEFAULT now()
    )
    ENGINE = MergeTree
    ORDER BY (timestamp, event_type)
    """,
    """
    CREATE TABLE IF NOT EXISTS metrics (
        metric_id UUID DEFAULT generateUUIDv4(),
        run_id String,
        lead_time_days Float64,
        false_alarm_rate Float64,
        severity_mae Float64,
        brier_score Float64,
        computed_at DateTime DEFAULT now()
    )
    ENGINE = MergeTree
    ORDER BY (run_id, computed_at)
    """,
]


def run_migrations(clickhouse: ClickHouseClient) -> None:
    for stmt in SCHEMA_STATEMENTS:
        clickhouse.command(stmt)
    LOGGER.info("ClickHouse schema migrations complete")
