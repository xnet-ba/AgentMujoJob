#!/usr/bin/env python3
"""Gradi backend kao samostalni izvršni fajl za Tauri bundl (PyInstaller).

Rezultat: desktop/src-tauri/binaries/agentmujojob-backend[.exe]
Pokreće se u CI-ju na windows-latest; lokalno radi i na Linuxu (za provjeru).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "desktop" / "src-tauri" / "binaries"
BUILD_DIR = ROOT / "build-sidecar"
NAME = "agentmujojob-backend"
EXT = ".exe" if sys.platform == "win32" else ""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable, "-m", "PyInstaller", "--onefile", "--noconfirm", "--clean",
            "--name", NAME,
            "--paths", str(ROOT / "backend"),
            "--collect-submodules", "uvicorn",
            "--distpath", str(BUILD_DIR),
            "--workpath", str(BUILD_DIR / "_work"),
            "--specpath", str(BUILD_DIR),
            str(ROOT / "backend" / "sidecar_entry.py"),
        ],
        check=True,
    )
    izvor = BUILD_DIR / (NAME + EXT)
    if not izvor.exists():
        raise SystemExit(f"PyInstaller nije proizveo {izvor}")
    odrediste = OUT_DIR / (NAME + EXT)
    shutil.copy2(izvor, odrediste)
    print(f"sidecar: {odrediste} ({odrediste.stat().st_size // 1024 // 1024} MB)")


if __name__ == "__main__":
    main()
