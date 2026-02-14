from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from pathlib import Path
from typing import Any

import boto3
from pydantic import BaseModel, ValidationError

from app.config import Settings


LOGGER = logging.getLogger(__name__)


class AgentBase:
    def __init__(
        self,
        settings: Settings,
        agent_name: str,
        prompt_file: str,
        output_model: type[BaseModel],
    ) -> None:
        self.settings = settings
        self.agent_name = agent_name
        self.output_model = output_model
        self._model_id = settings.agent_model_id(agent_name)
        prompt_path = Path(__file__).resolve().parent / "prompts" / prompt_file
        self.prompt_template = prompt_path.read_text(encoding="utf-8")
        self._bedrock = None
        if settings.use_bedrock:
            self._bedrock = boto3.client("bedrock-runtime", **settings.boto3_credentials())

    async def run(
        self,
        payload: dict[str, Any],
        rag_context: dict[str, Any] | None = None,
        strategy_notes: list[str] | None = None,
    ) -> BaseModel:
        prompt = self._build_prompt(payload=payload, rag_context=rag_context, strategy_notes=strategy_notes)

        if self._bedrock is not None:
            parsed = await self._run_bedrock_with_repair(prompt)
            if parsed is not None:
                try:
                    return self.output_model.model_validate(parsed)
                except ValidationError:
                    LOGGER.exception("%s output failed schema validation after Bedrock call", self.agent_name)

        fallback = self.local_fallback(payload=payload, rag_context=rag_context, strategy_notes=strategy_notes)
        return self.output_model.model_validate(fallback)

    def local_fallback(
        self,
        payload: dict[str, Any],
        rag_context: dict[str, Any] | None,
        strategy_notes: list[str] | None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def _build_prompt(
        self,
        payload: dict[str, Any],
        rag_context: dict[str, Any] | None,
        strategy_notes: list[str] | None,
    ) -> str:
        # Use compact JSON (no indent) to reduce token count
        prompt = (
            f"{self.prompt_template}\n\n"
            f"Output schema:\n{json.dumps(self.output_model.model_json_schema())}\n\n"
            f"Payload JSON:\n{json.dumps(payload, default=str)}\n\n"
            f"RAG JSON:\n{json.dumps(rag_context or {}, default=str)}\n\n"
            f"Strategy notes:\n{json.dumps(strategy_notes or [], default=str)}"
        )
        LOGGER.debug("%s prompt size: %d chars", self.agent_name, len(prompt))
        return prompt

    async def _run_bedrock_with_repair(self, prompt: str) -> dict[str, Any] | None:
        raw = await asyncio.to_thread(self._invoke_with_retry, prompt)
        parsed = _extract_json(raw)
        if parsed is not None:
            return parsed

        repair_prompt = (
            "Fix the following model output so it is valid JSON and matches the schema exactly. "
            "Return JSON only, no markdown.\n\n"
            f"Schema:\n{json.dumps(self.output_model.model_json_schema(), indent=2)}\n\n"
            f"Broken output:\n{raw}"
        )
        repaired = await asyncio.to_thread(self._invoke_with_retry, repair_prompt)
        return _extract_json(repaired)

    def _invoke_with_retry(self, prompt: str, max_attempts: int = 3) -> str:
        delay = 0.6
        for attempt in range(1, max_attempts + 1):
            try:
                return self._invoke_bedrock(prompt)
            except Exception:
                LOGGER.exception("%s Bedrock attempt %s/%s failed", self.agent_name, attempt, max_attempts)
                if attempt == max_attempts:
                    raise
                time.sleep(delay)
                delay *= 2
        raise RuntimeError("Unreachable")

    def _invoke_bedrock(self, prompt: str) -> str:
        model_id = self._model_id

        # ---------- build request body per provider ----------
        if "amazon.nova" in model_id:
            body: dict = {
                "schemaVersion": "messages-v1",
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {
                    "maxTokens": self.settings.bedrock_max_tokens,
                    "temperature": 0.1,
                },
            }
        else:
            # Anthropic / Claude format
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.settings.bedrock_max_tokens,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": prompt}],
            }

        response = self._bedrock.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
        payload = json.loads(response["body"].read())

        # ---------- parse response per provider ----------

        # Amazon Nova: {"output":{"message":{"content":[{"text":"..."}]}}}
        if isinstance(payload.get("output"), dict):
            msg = payload["output"].get("message", {})
            content = msg.get("content", [])
            parts: list[str] = [
                block["text"]
                for block in content
                if isinstance(block, dict) and block.get("text")
            ]
            if parts:
                return "\n".join(parts)

        # Anthropic: {"content":[{"text":"..."}]}
        if isinstance(payload.get("content"), list):
            parts = []
            for block in payload["content"]:
                if isinstance(block, dict) and block.get("text"):
                    parts.append(block["text"])
            return "\n".join(parts)

        # Titan / other
        if isinstance(payload.get("results"), list) and payload["results"]:
            first = payload["results"][0]
            text = first.get("outputText") if isinstance(first, dict) else None
            if text:
                return text

        if payload.get("output"):
            return str(payload["output"])

        return json.dumps(payload)


def _extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None

    stripped = text.strip()
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    stripped = re.sub(r"^```json", "", stripped, flags=re.IGNORECASE).strip()
    stripped = re.sub(r"```$", "", stripped).strip()

    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if not match:
        return None

    fragment = match.group(0)
    try:
        parsed = json.loads(fragment)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        return None

    return None
