import json, os
from typing import Any

class JsonStore:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def write(self, key: str, value: Any):
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data[key] = value
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
