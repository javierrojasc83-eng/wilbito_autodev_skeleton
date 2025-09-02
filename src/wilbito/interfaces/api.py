from fastapi import FastAPI
from .. import __version__

app = FastAPI(title="Wilbito API", version=__version__)

@app.get("/health")
def health():
    return {"ok": True, "version": __version__}

@app.get("/status")
def status():
    return {"status": "ready"}
