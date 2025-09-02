import subprocess, os

class QualityPipeline:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def run_checks(self) -> dict:
        results = {}
        try:
            subprocess.run(["pytest", "-q"], cwd=self.base_dir, check=True)
            results["tests"] = "ok"
        except Exception as e:
            results["tests"] = f"fail: {e}"
        try:
            subprocess.run(["python", "-m", "py_compile", os.path.join(self.base_dir, "src")], check=True)
            results["lint"] = "ok"
        except Exception as e:
            results["lint"] = f"fail: {e}"
        return results
