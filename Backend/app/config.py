from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SENTINEL Backend"
    env: str = "dev"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000

    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    clickhouse_host: str = "clickhouse"
    clickhouse_port: int = 8123
    clickhouse_username: str = "default"
    clickhouse_password: str = ""
    clickhouse_database: str = "sentinel"
    clickhouse_secure: bool = False

    aws_region: str = "us-west-2"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_session_token: str = ""

    use_bedrock: bool = False
    bedrock_chat_model_id: str = "us.amazon.nova-premier-v1:0"
    bedrock_max_tokens: int = 4096

    def boto3_credentials(self) -> dict[str, str]:
        """Return kwargs dict for boto3.client() with explicit credentials.
        Empty strings are omitted so boto3 falls back to its default chain."""
        creds: dict[str, str] = {"region_name": self.aws_region}
        if self.aws_access_key_id:
            creds["aws_access_key_id"] = self.aws_access_key_id
        if self.aws_secret_access_key:
            creds["aws_secret_access_key"] = self.aws_secret_access_key
        if self.aws_session_token:
            creds["aws_session_token"] = self.aws_session_token
        return creds

    # Per-agent model overrides (fall back to bedrock_chat_model_id)
    bedrock_ingest_model_id: str = ""
    bedrock_genomics_model_id: str = ""
    bedrock_epi_osint_model_id: str = ""
    bedrock_meta_model_id: str = ""

    use_bedrock_embeddings: bool = False
    bedrock_embedding_model_id: str = "amazon.titan-embed-text-v2:0"
    embedding_dim: int = 1024

    use_rerank: bool = False
    bedrock_rerank_model_id: str = "amazon.rerank-v1:0"

    dispatch_dry_run: bool = True

    run_default_cases: int = 20
    rag_top_k: int = 3
    max_vector_scan: int = 500

    guardrail_severity_threshold: float = 7.0
    guardrail_confidence_threshold_pct: float = 60.0

    outbreak_data_path: str = "data/outbreaks.jsonl"

    def agent_model_id(self, agent_name: str) -> str:
        """Resolve per-agent model ID, falling back to the global default."""
        overrides = {
            "ingest": self.bedrock_ingest_model_id,
            "genomics": self.bedrock_genomics_model_id,
            "epi_osint": self.bedrock_epi_osint_model_id,
            "meta": self.bedrock_meta_model_id,
        }
        specific = overrides.get(agent_name, "").strip()
        return specific if specific else self.bedrock_chat_model_id

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [v.strip() for v in self.cors_origins.split(",") if v.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
