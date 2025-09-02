from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from wilbito.memory.vectorstore import VectorStore

def write_entry(texto: str, tag: Optional[str] = None) -> Dict[str, Any]:
    """
    Escribe en memoria/diario_wilbito/YYYY/MM/diario_YYYYMMDD.md
    Devuelve dict con path; intenta auto-ingestar en vectorstore si hay tag.
    """
    base = Path("memoria") / "diario_wilbito"
    now = datetime.now()
    year = f"{now.year:04d}"
    month = f"{now.month:02d}"
    day = f"{now.day:02d}"

    ddir = base / year / month
    ddir.mkdir(parents=True, exist_ok=True)
    fp = ddir / f"diario_{year}{month}{day}.md"

    ts = now.isoformat()
    line = f"- {ts}: {texto}\n"
    with open(fp, "a", encoding="utf-8") as f:
        f.write(line)

    # Auto-ingesta si hay tag
    if tag:
        dbp = Path("memoria") / "vector_db" / "vectorstore.json"
        vs = VectorStore.load(str(dbp))
        # usa add_texts si existe, senón fallback a add_text
        if hasattr(vs, "add_texts"):
            vs.add_texts([{"text": texto, "meta": {"tag": tag, "source": "diario", "timestamp": ts, "file": str(fp)}}])
        else:
            vs.add_text(texto, {"tag": tag, "source": "diario", "timestamp": ts, "file": str(fp)})
        vs.save(str(dbp))

    return {"file": str(fp)}
