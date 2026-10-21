# Windows 11 build

Desktop = Tauri 2 omotač oko frontenda. `.msi`/`.exe` se grade u CI-ju
(`windows-build.yml`, `windows-latest`); lokalno je potreban Rust + Windows.

## Šta ulazi u instalaciju

| Dio | Kako nastaje |
|---|---|
| Frontend | `scripts/tauri-export-build.js` → `frontend/out/` (statički export) |
| Backend | `scripts/build-backend-sidecar.py` → PyInstaller `agentmujojob-backend.exe` u `desktop/src-tauri/binaries/` |
| OpenCode CLI | CI preuzima pinovanu `opencode-windows-x64` arhivu → `desktop/src-tauri/binaries/opencode.exe` |
| Tauri ljuska | `tauri-action` (`projectPath: desktop`) → `.msi` + NSIS `.exe` |

`desktop/src-tauri/tauri.conf.json` uključuje `binaries/*` kao `bundle.resources`.
Binarni fajlovi se ne commit-uju (`.gitignore`), samo `.gitkeep`.

## Ponašanje pri radu

- Rust (`src/lib.rs`) pri startu pokreće `agentmujojob-backend.exe` sa
  `BACKEND_HOST=127.0.0.1`, `BACKEND_PORT=8010`, `CORS_ORIGINS` za Tauri origin
  i `OPENCODE_BIN` koji pokazuje na bundlani `opencode.exe`.
- Backend se gasi pri izlasku aplikacije (`RunEvent::Exit`).
- Frontend pri otvaranju polluje `/api/health` dok servis ne proradi; do tada je
  dugme onemogućeno („Pokrećem servis…").
- Ako OpenCode nije povezan (`opencode auth login`), pretraga se izvodi lokalnim
  parserom ključnih riječi, a odgovor to navodi u `ai_napomena`.

## Potpisivanje

Nema certifikata — SmartScreen može upozoriti. Ne dodavati tajne u workflow.
