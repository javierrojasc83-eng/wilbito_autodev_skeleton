## V3 - Calidad, Versionado y Release

Comandos nuevos:
- `python -m wilbito.interfaces.cli quality` → valida sintaxis de artifacts/codegen/*.py
- `python -m wilbito.interfaces.cli pr --objetivo "X"` → comentarios de revisión del Consejo
- `python -m wilbito.interfaces.cli release --bump patch|minor|major` → zip + changelog + bump versión
