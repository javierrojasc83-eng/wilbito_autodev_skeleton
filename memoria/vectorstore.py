@'
import os
import re
import json
import math
import uuid
import shutil
import datetime
from collections import Counter
from typing import List, Dict, Any, Optional

_WORD_RE = re.compile(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ0-9]+")

def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in _WORD_RE.findall(text or "")]

def _cosine(a: Counter, b: Counter) -> float:
    num = 0.0
    for k, v in a.items():
        if k in b:
            num += v * b[k]
    sa = math.sqrt(sum(v * v for v in a.values()))
    sb = math.sqrt(sum(v * v for v in b.values()))
    if sa == 0.0 or sb == 0.0:
        return 0.0
    return num / (sa * sb)

class VectorStore:
    """
    VectorStore simple sin dependencias externas.
    - Almacena ítems con: id, text, meta, ts.
    - Similaridad por coseno con TF (Counter).
    - Persiste/recupera desde JSON.
    """
    def __init__(self, items: Optional[List[Dict[str, Any]]] = None):
        self.items: List[Dict[str, Any]] = items or []

    def add(self, text: str, meta: Optional[Dict[str, Any]] = None) -> str:
        item_id = str(uuid.uuid4())
        self.items.append({
            "id": item_id,
            "text": text,
            "meta": meta or {},
            "ts": datetime.datetime.utcnow().isoformat() + "Z",
        })
        return item_id

    def to_dict(self) -> Dict[str, Any]:
        return {"items": self.items}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VectorStore":
        return cls(items=list(data.get("items") or []))

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> "VectorStore":
        if not os.path.exists(path):
            return cls()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def backup(self, db_path: str, backups_dir: str) -> Dict[str, str]:
        if not os.path.exists(db_path):
            return {"ok": "false", "error": f"No existe {db_path}"}
        os.makedirs(backups_dir, exist_ok=True)
        ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        dst = os.path.join(backups_dir, f"vectorstore_{ts}.json")
        shutil.copy2(db_path, dst)
        latest = os.path.join(backups_dir, "vectorstore_latest.json")
        shutil.copy2(db_path, latest)
        return {"ok": "true", "backup": dst, "latest": latest}

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        q_tokens = Counter(_tokenize(query))
        scores = []
        for it in self.items:
            d_tokens = Counter(_tokenize(it.get('text', '')))
            score = _cosine(q_tokens, d_tokens)
            scores.append((score, it))
        scores.sort(key=lambda x: x[0], reverse=True)
        out = []
        for score, it in scores[:max(1, top_k)]:
            out.append({
                "id": it["id"],
                "score": round(float(score), 4),
                "text": it.get("text", ""),
                "meta": it.get("meta", {}),
            })
        return out

    def ingest_jsonl(self, path: str) -> int:
        if not os.path.exists(path):
            raise FileNotFoundError(f"No existe {path}")
        count = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    text = obj.get("text", "")
                    tag = obj.get("tag")
                    meta = {"tag": tag} if tag else {}
                    self.add(text, meta)
                    count += 1
                except Exception:
                    continue
        return count
'@ | Set-Content .\src\wilbito\memory\vectorstore.py -Encoding UTF8
