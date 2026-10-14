# Appwrite setup (https://baza.kolektiv.pro, v1.8.1)

1. U postojećoj instanci napravi **odvojenu bazu** `agentmujojob` (ili prefiks `amj_` ako se koristi zajednička) — ne diraj tuđe kolekcije.
2. Kreiraj kolekcije `jobs`, `job_sources`, `scan_runs` po `appwrite/schema.json` (unique index na `original_url`).
3. Napravi API ključ s najmanjim privilegijama (samo ta baza) i upiši `APPWRITE_*` u `backend/.env`.
4. Pokreni `python3 appwrite/migrate.py` — idempotentno, bez ključa samo ispiše upute i ne tvrdi ništa.
5. Admin ključ nikad u frontend/desktop.
