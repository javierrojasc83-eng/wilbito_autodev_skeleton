import os
import shutil
import datetime

def backup_vectorstore(db_dir: str = "memoria/vector_db", backup_dir: str | None = None):
    """
    Copia memoria/vector_db/vectorstore.json a memoria/vector_db/backups/vectorstore_YYYYmmddHHMMSS.json
    y además actualiza backups/vectorstore_latest.json
    """
    if backup_dir is None:
        backup_dir = os.path.join(db_dir, "backups")

    os.makedirs(backup_dir, exist_ok=True)
    src = os.path.join(db_dir, "vectorstore.json")
    if not os.path.exists(src):
        return {"ok": False, "error": f"No existe {src}"}

    ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    dst = os.path.join(backup_dir, f"vectorstore_{ts}.json")
    shutil.copy2(src, dst)

    latest = os.path.join(backup_dir, "vectorstore_latest.json")
    shutil.copy2(src, latest)

    return {"ok": True, "backup": dst, "latest": latest}
