from __future__ import annotations

import logging
import re
from typing import Any, Sequence

import clickhouse_connect
from clickhouse_connect.driver.client import Client

from app.config import Settings


LOGGER = logging.getLogger(__name__)


class ClickHouseClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: Client | None = None

    @property
    def client(self) -> Client:
        if self._client is None:
            raise RuntimeError("ClickHouse client is not connected")
        return self._client

    def connect(self) -> None:
        if self._client is not None:
            return

        safe_db = self._safe_identifier(self.settings.clickhouse_database)

        connect_kwargs = dict(
            host=self.settings.clickhouse_host,
            port=self.settings.clickhouse_port,
            username=self.settings.clickhouse_username,
            password=self.settings.clickhouse_password,
            secure=self.settings.clickhouse_secure,
        )

        bootstrap = clickhouse_connect.get_client(**connect_kwargs, database="default")
        bootstrap.command(f"CREATE DATABASE IF NOT EXISTS {safe_db}")
        bootstrap.close()

        self._client = clickhouse_connect.get_client(**connect_kwargs, database=safe_db)
        LOGGER.info("Connected to ClickHouse database '%s'", safe_db)

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def command(self, sql: str, parameters: dict[str, Any] | None = None) -> None:
        self._validate_sql(sql)
        self.client.command(sql, parameters=parameters)

    def query_dicts(self, sql: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        self._validate_sql(sql)
        result = self.client.query(sql, parameters=parameters)
        return [dict(zip(result.column_names, row)) for row in result.result_rows]

    def insert(self, table: str, rows: Sequence[Sequence[Any]], column_names: Sequence[str]) -> None:
        if not rows:
            return
        safe_table = self._safe_identifier(table)
        self.client.insert(table=safe_table, data=list(rows), column_names=list(column_names))

    @staticmethod
    def _safe_identifier(name: str) -> str:
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            raise ValueError(f"Unsafe SQL identifier: {name}")
        return name

    @staticmethod
    def _validate_sql(sql: str) -> None:
        trimmed = sql.strip()
        if not trimmed:
            raise ValueError("SQL cannot be empty")
        if ";" in trimmed.rstrip(";"):
            raise ValueError("Multiple SQL statements are not allowed")
