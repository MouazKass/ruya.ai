from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    dot = sum(a[i] * b[i] for i in range(n))
    norm_a = math.sqrt(sum(v * v for v in a[:n])) or 1.0
    norm_b = math.sqrt(sum(v * v for v in b[:n])) or 1.0
    return float(dot / (norm_a * norm_b))


@dataclass(slots=True)
class IndexedItem:
    item_id: str
    payload: dict[str, Any]
    embedding: list[float]


class InMemoryVectorIndex:
    def __init__(self) -> None:
        self._items: list[IndexedItem] = []

    def clear(self) -> None:
        self._items = []

    def add(self, item_id: str, payload: dict[str, Any], embedding: list[float]) -> None:
        self._items.append(IndexedItem(item_id=item_id, payload=payload, embedding=embedding))

    def bulk_add(self, items: list[IndexedItem]) -> None:
        self._items.extend(items)

    def search(self, query_embedding: list[float], k: int) -> list[dict[str, Any]]:
        scored = []
        for item in self._items:
            similarity = cosine_similarity(query_embedding, item.embedding)
            scored.append({"item_id": item.item_id, "similarity": similarity, "payload": item.payload})
        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:k]
