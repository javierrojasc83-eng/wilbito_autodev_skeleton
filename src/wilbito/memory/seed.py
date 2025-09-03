import importlib
import json
import os

from .vectorstore import VectorStore


def _load_items(path: str):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".yaml", ".yml"):
        # Intento de import de PyYAML real (no otros 'yaml' raros)
        try:
            yaml = importlib.import_module("yaml")
            if not hasattr(yaml, "safe_load"):
                raise ImportError("El módulo 'yaml' cargado no es PyYAML.")
        except Exception as e:
            raise RuntimeError(
                "El archivo de semillas es YAML pero PyYAML no está disponible. Instalá con: pip install PyYAML"
            ) from e
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    else:
        # JSON por defecto
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("El archivo de semillas debe ser una lista de objetos {text, tag}.")

    items = []
    for obj in data:
        if not isinstance(obj, dict):
            continue
        text = obj.get("text") or obj.get("contenido") or obj.get("nota")
        tag = obj.get("tag") or obj.get("etiqueta") or obj.get("label")
        if text:
            items.append({"text": text, "meta": {"tag": tag} if tag else {}})
    return items


def seed_from_file(path: str, db_dir: str = "memoria/vector_db"):
    vs = VectorStore(db_dir)
    items = _load_items(path)
    for it in items:
        vs.add_text(it["text"], it["meta"])
    vs.save()
    return {"ok": True, "ingested": len(items), "db_dir": db_dir, "file": path}
