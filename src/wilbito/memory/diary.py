import os
from datetime import datetime


class Diario:
    def __init__(self, base_path: str):
        self.base_path = base_path

    def escribir(self, texto: str) -> str:
        y = datetime.utcnow().strftime("%Y")
        m = datetime.utcnow().strftime("%m")
        d = datetime.utcnow().strftime("%d")
        folder = os.path.join(self.base_path, y, m)
        os.makedirs(folder, exist_ok=True)
        fn = os.path.join(folder, f"diario_{y}{m}{d}.md")
        with open(fn, "a", encoding="utf-8") as f:
            f.write(texto.strip() + "\n\n")
        return fn
