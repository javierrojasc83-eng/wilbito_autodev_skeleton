import os
from typing import Dict, Any
from rich import print

class SafetyGate:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg

    def check_kill_switch(self) -> bool:
        kill_file = self.cfg.get("kill_switch_file", ".wilbito_stop")
        exists = os.path.exists(kill_file)
        if exists:
            print("[red]KILL SWITCH activado. Abortando.[/red]")
        return exists

    def require_human(self) -> bool:
        return bool(self.cfg.get("human_gate_required", True))
