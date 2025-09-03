import datetime
import json
import os
import zipfile


def _load_version(vpath):
    if not os.path.exists(vpath):
        return [0, 1, 0]
    with open(vpath, encoding="utf-8") as f:
        return json.load(f).get("version") or [0, 1, 0]


def _save_version(vpath, version):
    os.makedirs(os.path.dirname(vpath), exist_ok=True)
    with open(vpath, "w", encoding="utf-8") as f:
        json.dump(
            {"version": version, "updated": datetime.datetime.utcnow().isoformat() + "Z"},
            f,
            indent=2,
        )


def _bump(kind, version):
    major, minor, patch = version
    if kind == "major":
        return [major + 1, 0, 0]
    if kind == "minor":
        return [major, minor + 1, 0]
    return [major, minor, patch + 1]


def run_release(bump: str = "patch"):
    base_dir = os.getcwd()
    vpath = os.path.join(base_dir, "artifacts", "version.json")
    ver = _bump(bump, _load_version(vpath))
    _save_version(vpath, ver)
    ver_str = ".".join(map(str, ver))

    ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    changelog = os.path.join(base_dir, "CHANGELOG.md")
    with open(changelog, "a", encoding="utf-8") as f:
        f.write(f"## {ver_str} - {ts}\n- Release automática de artefactos mínimos.\n\n")

    zip_path = os.path.join(base_dir, "artifacts", f"release_{ver_str}_{ts}.zip")
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    src_root = os.path.join(base_dir, "src")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(src_root):
            for fn in files:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, base_dir)
                z.write(full, arcname=rel)
    return {"version": ver_str, "zip": zip_path, "changelog": changelog}
