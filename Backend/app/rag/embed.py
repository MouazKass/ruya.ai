from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from typing import Any

import boto3

from app.config import Settings


LOGGER = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._bedrock_client = None
        if settings.use_bedrock_embeddings:
            self._bedrock_client = boto3.client("bedrock-runtime", **settings.boto3_credentials())

    def embed_text(self, text: str) -> list[float]:
        if self._bedrock_client is not None:
            try:
                return self._embed_with_bedrock(text)
            except Exception:
                LOGGER.exception("Bedrock embedding failed, using deterministic local embedding")
        return self._embed_locally(text)

    def _embed_with_bedrock(self, text: str) -> list[float]:
        body = json.dumps({"inputText": text})
        response = self._bedrock_client.invoke_model(
            modelId=self.settings.bedrock_embedding_model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        payload = json.loads(response["body"].read())
        vector = payload.get("embedding") or payload.get("embeddings")
        if isinstance(vector, list) and vector and isinstance(vector[0], list):
            vector = vector[0]
        if not isinstance(vector, list):
            raise ValueError("Embedding model did not return an embedding list")
        normalized = [float(v) for v in vector]
        return self._fit_dim(normalized)

    def _embed_locally(self, text: str) -> list[float]:
        dim = self.settings.embedding_dim
        tokens = re.findall(r"[a-z0-9_]+", text.lower())
        vector = [0.0] * dim

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "big") % dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            weight = 1.0 + (digest[5] / 255.0)
            vector[idx] += sign * weight

        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [float(v / norm) for v in vector]

    def _fit_dim(self, vector: list[float]) -> list[float]:
        dim = self.settings.embedding_dim
        if len(vector) == dim:
            return [float(v) for v in vector]
        if len(vector) > dim:
            vector = vector[:dim]
        else:
            vector = vector + [0.0] * (dim - len(vector))

        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [float(v / norm) for v in vector]


def case_to_embedding_text(case_payload: dict[str, Any]) -> str:
    parts = [
        str(case_payload.get("case_id", "")),
        str(case_payload.get("country", "")),
        str(case_payload.get("city", "")),
        str(case_payload.get("pathogen_label", "")),
    ]

    genomic = case_payload.get("genomic", {})
    epi = case_payload.get("epi_osint", {})
    geo = case_payload.get("geo", {})

    parts.extend(
        [
            str(genomic.get("mutation_novelty", "")),
            str(genomic.get("lineage_deviation", "")),
            str(genomic.get("recombination_flag", "")),
            str(epi.get("anomaly_score", "")),
            str(epi.get("reliability_hint", "")),
            " ".join(epi.get("source_types", []) or []),
            " ".join(epi.get("news_snippets", []) or []),
            str(geo.get("travel_hub_score", "")),
            str(geo.get("population_density_score", "")),
            str(geo.get("border_connectivity", "")),
        ]
    )

    return " | ".join(parts)
