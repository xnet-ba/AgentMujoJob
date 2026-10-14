# AgentMujoJob

Open-source AI asistent za pronalazak posla. Bosanski (ijekavica).

**Naslov:** Pronađi posao koji ti odgovara.
**Podnaslov:** Pretraži oglase u BiH, regionu i svijetu uz pomoć AI asistenta.

## Stanje implementacije

- Backend API (FastAPI): `/api/health`, `/api/jobs`, `/api/jobs/{id}`, `/api/search`, `/api/sources`, `/api/sources/health`, `/api/admin/*` — implementirano i testirano.
- Konektori: `greenhouse-eu` (provjereno radi — javni Greenhouse boards API), generički `RssKonektor` adapter (čeka provjeren feed URL).
- Normalizacija, deduplikacija, rangiranje, deterministički AI fallback — implementirano i testirano.
- Web frontend (Next.js, bosanski) — implementiran.
- Desktop (Tauri 2, Windows .msi) — konfiguracija + CI workflow; artefakt nastaje na `windows-latest` runneru.
- Appwrite: schema + idempotentna `migrate.py`; kolekcije se kreiraju tek uz kredencijale (vidi `docs/APPWRITE-SETUP.md`).
- Bez registracije korisnika, bez CV-jeva, bez historije pretrage — po dizajnu.

## Brzi start (backend)

```bash
cd backend && python3 -m venv venv && venv/bin/pip install -r requirements.txt
cp ../.env.example .env   # unesi ADMIN_TOKEN
venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8010
venv/bin/python -m pytest -q
```

Frontend: `cd frontend && npm install && npm run dev` (uz `NEXT_PUBLIC_API_URL` prema backendu).

Detalji: `docs/ARHITEKTURA.md`, `docs/KONEKTORI.md`, `docs/HESTIA-DEPLOY.md`, `docs/WINDOWS-BUILD.md`, `docs/SIGURNOST.md`.
