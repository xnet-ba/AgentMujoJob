# Hestia deploy (uz odobrenje — ništa nije mijenjano)

Preduvjet: dogovorena domena (placeholder `__DOMENA__`). Koraci: 1. Kopiraj repo u `/home/sha/AgentMujoJob`, napravi venv, `backend/.env`. 2. `systemd enable deploy/hestia/agentmujojob.service` (samo 127.0.0.1:8010, bez izloženih portova). 3. U Hestia web domeni dodaj `deploy/hestia/nginx-snippet.conf` kao proxy (frontend :3000, `/api/` → :8010). 4. Health: `curl 127.0.0.1:8010/api/health`. Rollback: `systemctl stop agentmujojob`, prethodni direktorij. Backup: `backend/data/` + `.env` (van repoa).
