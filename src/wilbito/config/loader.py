from __future__ import annotations

import os
from pathlib import Path

# Intento robusto de obtener safe_load desde PyYAML
# Evita colisiones con reportlab.lib.yaml (que NO tiene safe_load)
try:
    from yaml import safe_load as _yaml_safe_load  # type: ignore

    _HAS_PYYAML = True
except Exception:
    _yaml_safe_load = None  # type: ignore
    _HAS_PYYAML = False

DEFAULTS = {
    "router": {
        "max_iter_default": 1,
        "top_k_default": 5,
        "use_context_default": False,
    },
    "council": {
        "max_iter_default": 2,
        "granularity_default": "coarse",
        "top_k_default": 5,
        "use_context_default": False,
    },
}


def _load_yaml_dict(fp: Path) -> dict:
    """
    Carga YAML de forma segura si PyYAML está disponible.
    Si no lo está, devuelve {} para que se usen defaults.
    """
    if not fp.exists():
        return {}
    if not _HAS_PYYAML:
        # Sin PyYAML: ignora el archivo y usa defaults.
        return {}
    try:
        with fp.open("r", encoding="utf-8") as f:
            data = _yaml_safe_load(f) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        # YAML inválido o error de parseo → ignora y usa defaults.
        return {}


def load_config() -> dict:
    """
    Lee config/agents.yaml si existe (y si hay PyYAML).
    Mezcla con DEFAULTS (defaults como base, config de archivo por encima).
    """
    base_dir = Path(os.getcwd())
    cfg_dir = base_dir / "config"
    cfg_path = cfg_dir / "agents.yaml"

    file_cfg = _load_yaml_dict(cfg_path)
    # Merge simple (2 niveles) → archivo pisa defaults
    merged = {}
    # Copia defaults
    for k, v in DEFAULTS.items():
        merged[k] = dict(v) if isinstance(v, dict) else v
    # Pisa con archivo
    for k, v in file_cfg.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k].update(v)
        else:
            merged[k] = v
    return merged


def get_default(cfg: dict, section_or_path: str, key: str | None = None, default=None):
    """
    Devuelve un valor por defecto desde la config en dos modos:

    1) Sección + clave:
       get_default(cfg, "router", "max_iter_default", 1)

    2) Ruta con puntos:
       get_default(cfg, "router.max_iter_default", 1)

    Nota: el 2º modo se detecta cuando 'key' es None.
    """
    # Modo ruta con puntos (key es None y tercer argumento es default)
    if key is None:
        # section_or_path es una ruta tipo "router.max_iter_default"
        path = section_or_path
        # Si llamaron con: get_default(cfg, "router.max_iter_default", 1)
        # entonces 'default' ya es el 3er argumento.
        parts = str(path).split(".")
        node = cfg
        for p in parts:
            if not isinstance(node, dict) or p not in node:
                return default
            node = node[p]
        return node

    # Modo sección + clave
    section = cfg.get(section_or_path)
    if isinstance(section, dict):
        return section.get(key, default)
    return default
