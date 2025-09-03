from __future__ import annotations

import json
import math
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


class VectorStore:
    """
    VectorStore mínimo basado en bag-of-words + TF-IDF estático simple.
    Almacena:
      - items: List[Dict]: {id, text, meta}
    Persistencia en JSON: {"items":[...]}
    """

    def __init__(self, items: list[dict[str, Any]] | None = None):
        self.items: list[dict[str, Any]] = items or []

    # ---------- Persistencia ----------
    @classmethod
    def load(cls, path: str) -> VectorStore:
        p = Path(path)
        if not p.exists():
            # base vacía
            return cls([])
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            items = data.get("items", [])
            if not isinstance(items, list):
                items = []
            return cls(items)
        except Exception:
            # archivo inválido → iniciar vacío (no reventamos)
            return cls([])

    def save(self, path: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {"items": self.items}
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---------- Ingesta ----------
    def add_text(self, text: str, meta: dict[str, Any] | None = None) -> bool:
        if not text or not isinstance(text, str):
            return False
        self.items.append({"id": str(uuid.uuid4()), "text": text, "meta": meta or {}})
        return True

    def add_texts(self, entries: list[dict[str, Any]]) -> int:
        """
        entries: List[{"text": str, "meta": dict}]
        """
        n = 0
        for e in entries:
            t = e.get("text")
            m = e.get("meta", {})
            if self.add_text(t, m):
                n += 1
        return n

    # ---------- Búsqueda ----------
    def _tokenize(self, s: str) -> list[str]:
        return [tok.lower() for tok in s.replace("\n", " ").split() if tok.strip()]

    def _bow(self, s: str) -> dict[str, float]:
        # Conteo simple
        bag: dict[str, float] = {}
        for t in self._tokenize(s):
            bag[t] = bag.get(t, 0.0) + 1.0
        # Normalización L2 para similitud coseno simple
        norm = math.sqrt(sum(v * v for v in bag.values())) or 1.0
        for k in list(bag.keys()):
            bag[k] /= norm
        return bag

    def _cosine(self, a: dict[str, float], b: dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        # producto punto en intersección
        keys = set(a.keys()) & set(b.keys())
        return sum(a[k] * b[k] for k in keys)

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        prefer_tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        prefer_tags: si se provee, se aplica un pequeño boost al score
        """
        qv = self._bow(query)
        out = []
        for it in self.items:
            tv = self._bow(it.get("text", ""))
            score = self._cosine(qv, tv)

            # Boost por tag preferido
            meta = it.get("meta", {}) or {}
            item_tag = meta.get("tag")
            if prefer_tags and item_tag in prefer_tags:
                score *= 1.2  # boost suave

            if score >= (min_score or 0.0):
                out.append(
                    {
                        "id": it.get("id"),
                        "score": round(float(score), 4),
                        "text": it.get("text", ""),
                        "meta": meta,
                    }
                )

        out.sort(key=lambda x: x["score"], reverse=True)
        return out[: max(1, top_k)]
