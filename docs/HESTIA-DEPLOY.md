# Hestia deploy — posao.kolektiv.pro

Status 2026-10-14: **DNS zapis za `posao.kolektiv.pro` ne postoji** (NXDOMAIN; `kolektiv.pro` → 185.255.131.101).
Nalog `sha` nema prava nad Hestia panelom (`/usr/local/hestia/data/users/` — Permission denied, bez sudo),
pa domenu, DNS i proxy mora kreirati vlasnik panela. Ispod su tačni koraci — ništa nije mijenjano.

## Korak 1 — DNS (registrar ili Hestia DNS)

```
posao.kolektiv.pro.  300  IN  A  185.255.131.101
```

Provjera: `dig +short posao.kolektiv.pro` → mora vratiti `185.255.131.101`.

## Korak 2 — Hestia web domena

U HestiaCP (vlasnik panela): Web → Add Web Domain → `posao.kolektiv.pro` → Enable SSL (Let's Encrypt) →
u polje proxy/snippet dodati sadržaj `deploy/hestia/nginx-snippet.conf`.

## Korak 3 — Backend servis (korisnik sha, bez root prava)

```bash
cd /home/sha/AgentMujoJob/backend
python3 -m venv venv && venv/bin/pip install -r requirements.txt
cp ../.env.example .env   # unesi ADMIN_TOKEN + (kad stigne) APPWRITE_*
# servis pokreće vlasnik panela ILI sudo:
cp ../deploy/hestia/agentmujojob.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now agentmujojob
```

Servis sluša samo `127.0.0.1:8010` (vidi `deploy/hestia/agentmujojob.service`).

## Korak 4 — Frontend (PM2, korisnik sha)

```bash
cd /home/sha/AgentMujoJob/frontend && npm install && npm run build
NEXT_PUBLIC_API_URL=https://posao.kolektiv.pro pm2 start npm --name posao-web -- start -- -p 3000
pm2 save
```

Frontend sluša samo `127.0.0.1:3000` (dodati `--hostname 127.0.0.1` ako treba).

## Korak 5 — Provjera

```bash
curl http://127.0.0.1:8010/api/health          # {"status":"ok",...}
curl -s https://posao.kolektiv.pro/api/health  # isto kroz proxy
curl -s https://posao.kolektiv.pro/ -o /dev/null -w '%{http_code}\n'  # 200
```

## Backup / rollback / nadogradnja

- Backup: `backend/data/*.json` + `backend/.env` (čuvati VAN repoa) + `pm2 save`.
- Rollback: `systemctl stop agentmujojob`, `pm2 stop posao-web`, vratiti prethodni `git checkout <sha>`.
- Nadogradnja: `git pull && backend/venv/bin/pip install -r backend/requirements.txt && systemctl restart agentmujojob && pm2 restart posao-web`.
- Log rotacija: journald (servis) + `pm2 install pm2-logrotate`.
