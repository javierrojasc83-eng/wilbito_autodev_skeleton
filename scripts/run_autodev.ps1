param([string]$Objetivo = "mejorar el agente de codegen", [int]$MaxIter = 1)
python -m wilbito.interfaces.cli autodev --objetivo "$Objetivo" --max-iter $MaxIter
