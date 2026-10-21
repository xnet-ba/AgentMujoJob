"""Ulazna točka za PyInstaller sidecar (Windows .msi).

PyInstaller pakira ovaj fajl u samostalni `agentmujojob-backend.exe`; Tauri ga
pokreće pri startu aplikacije. Nema CLI argumenata — sve dolazi iz environmenta.
"""
from __future__ import annotations

import os

import uvicorn

from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.environ.get("BACKEND_HOST", "127.0.0.1"),
        port=int(os.environ.get("BACKEND_PORT", "8010") or 8010),
        log_level=os.environ.get("LOG_LEVEL", "warning"),
    )
