import os

VERSION_FILE = os.path.join(os.path.dirname(__file__), "..", "VERSION")


def read_version() -> str:
    if not os.path.exists(VERSION_FILE):
        return "0.1.0"
    with open(VERSION_FILE, encoding="utf-8") as f:
        return f.read().strip()


def bump_version(bump: str = "patch") -> str:
    version = read_version()
    major, minor, patch = (int(x) for x in version.split("."))
    if bump == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1
    new_version = f"{major}.{minor}.{patch}"
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(new_version)
    return new_version
