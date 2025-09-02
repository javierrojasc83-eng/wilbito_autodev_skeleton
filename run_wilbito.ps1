$env:PYTHONNOUSERSITE = "1"
$env:PYTHONPATH = $null
# Activa el venv (ajusta la ruta si estás en otra carpeta)
& "..\wilbito-env\Scripts\Activate.ps1"

# Reinstala editable por si tocaste código
python -m pip install -e .

# Muestra ayuda
python -m wilbito.interfaces.cli --help
