import os, datetime
from ..tools.versioning import bump_version

class ReleasePipeline:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def create_release(self, bump: str = "patch") -> str:
        version = bump_version(bump)
        changelog = os.path.join(self.base_dir, "CHANGELOG.md")
        with open(changelog, "a", encoding="utf-8") as f:
            f.write(f"\n## {version} - {datetime.date.today()}\n- Release auto-generada.\n")
        return version
