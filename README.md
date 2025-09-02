# Wilbito Autodev Skeleton

Proyecto base para una IA de **autodesarrollo** con arquitectura por capas, CLI, API y configuración declarativa.

## Comandos rápidos
```powershell
# 1) Crear/activar venv
python -m venv wilbito-env
.\wilbito-env\Scripts\activate

# 2) Instalar en modo editable
pip install -U pip
pip install -e .

# 3) Probar CLI
python -m wilbito.interfaces.cli --help

# 4) Correr API
uvicorn wilbito.interfaces.api:app --reload --port 8000
```
