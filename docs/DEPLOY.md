# Produkcijski deploy (Linux, systemd + nginx reverse proxy)

Backend sluša samo `127.0.0.1:8010`, frontend samo `127.0.0.1:3000`; javnosti se
ne izlažu interni portovi. Potrebna je javna domena s TLS certifikatom.

## Korak 1 — DNS

```
VAS_DOMENA.  300  IN  A  VAS_SERVER_IP
```

Provjera: `dig +short VAS_DOMENA` → mora vratiti IP servera.

## Korak 2 — Reverse proxy

U nginx konfiguraciju domene dodati sadržaj `deploy/linux/nginx-snippet.conf`
(uz zamjenu `__DOMENA__`), s važećim TLS certifikatom (npr. Let's Encrypt).

## Korak 3 — Backend servis

```bash
sudo useradd -r -m -d /opt/agentmujojob agentmujojob
sudo cp -r . /opt/agentmujojob && sudo chown -R agentmujojob /opt/agentmujojob
cd /opt/agentmujojob/backend
python3 -m venv venv && venv/bin/pip install -r requirements.txt
cp ../.env.example .env   # unesi ADMIN_TOKEN (jedina tajna; nema baze ni API ključeva)
sudo cp ../deploy/linux/agentmujojob.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now agentmujojob
```

## Korak 4 — Frontend

```bash
cd /opt/agentmujojob/frontend && npm install && npm run build
NEXT_PUBLIC_API_URL=https://VAS_DOMENA pm2 start npm --name agentmujojob-web -- start -- -p 3000
pm2 save
```

Frontend se gradi uz `NEXT_PUBLIC_API_URL` prema javnoj domeni (bez nje default je localhost).

## Korak 5 — Provjera

```bash
curl http://127.0.0.1:8010/api/health            # {"status":"ok",...}
curl -s https://VAS_DOMENA/api/health            # isto kroz proxy
curl -s https://VAS_DOMENA/ -o /dev/null -w '%{http_code}\n'  # 200
```

## AI jezgro na serveru (jednokratno)

```bash
opencode auth login   # prijava za besplatne modele, van aplikacije
opencode models       # izbor modela -> OPENCODE_MODEL u backend/.env
```

Aplikacija ne posjeduje API ključeve; `opencode run` radi bez `--auto` (nikakva odobrenja alata).

## Backup / rollback / nadogradnja

- Backup: `backend/.env` (čuvati VAN repoa — jedina datoteka s tajnama). Podaci se ne backupuju: sve je u memoriji i nestaje gašenjem.
- Rollback: `systemctl stop agentmujojob`, vratiti prethodni `git checkout <sha>`.
- Nadogradnja: `git pull && backend/venv/bin/pip install -r backend/requirements.txt && systemctl restart agentmujojob`.
