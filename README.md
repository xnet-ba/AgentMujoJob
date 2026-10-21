# AgentMujoJob — Pronađi posao koji ti odgovara.

**Pretraži oglase u BiH, regionu i svijetu uz pomoć AI asistenta.**

Open-source AI asistent za pronalazak posla — **lokalno na Windowsu 11**. Jedan `.msi` nosi backend, interfejs i besplatni AI model: nema servera, naloga ni slanja podataka trećim licima. Interfejs i dokumentacija: **bosanski jezik, ijekavica**. Bez registracije, bez CV-jeva, bez historije pretrage — po dizajnu, ne kao naknadna opcija.

![CI](https://github.com/xnet-ba/AgentMujoJob/actions/workflows/tests.yml/badge.svg)
![Windows build](https://github.com/xnet-ba/AgentMujoJob/actions/workflows/windows-build.yml/badge.svg)
![Licenca](https://img.shields.io/badge/licenca-MIT-zeleno)
![Python](https://img.shields.io/badge/backend-FastAPI%20%E2%80%A2%20Python%203.12-plavo)
![Frontend](https://img.shields.io/badge/frontend-Next.js%2014%20%E2%80%A2%20TypeScript-plavo)
![Desktop](https://img.shields.io/badge/desktop-Tauri%202%20%E2%80%A2%20Windows%2011-svijetloplavo)

> **HTML verzija ovog dokumenta:** [`docs/index.html`](docs/index.html) — isti sadržaj u profesionalnom formatu za pregled u browseru.

![AgentMujoJob — pretraga kuhara u Sarajevu](docs/screenshot.png)

---

## Sadržaj

1. [Šta je AgentMujoJob](#šta-je-agentmujojob)
2. [Ključne karakteristike](#ključne-karakteristike)
3. [Kako radi](#kako-radi)
4. [Brzi start](#brzi-start)
5. [API referenca](#api-referenca)
6. [Izvori oglasa](#izvori-oglasa)
7. [AI pretraga i rangiranje](#ai-pretraga-i-rangiranje)
8. [Privatnost](#privatnost)
9. [Sigurnost](#sigurnost)
10. [Anonimnost: bez perzistencije](#anonimnost-bez-perzistencije)
11. [Windows 11 aplikacija](#windows-11-aplikacija)
12. [Lokalno pokretanje](#lokalno-pokretanje)
13. [Testiranje](#testiranje)
14. [Struktura projekta](#struktura-projekta)
15. [Status i poznata ograničenja](#status-i-poznata-ograničenja)
16. [Doprinos](#doprinos)
17. [Licenca](#licenca)

---

## Šta je AgentMujoJob

AgentMujoJob je besplatan, open-source asistent koji:

- **pretražuje oglase** za posao iz više izvora i normalizira ih u jedinstven format,
- **razumije prirodni jezik** — npr. „Tražim posao terenskog komercijaliste u Tešnju ili okolini, plata najmanje 1.800 KM, mogu putovati”,
- **rangira rezultate** po relevantnosti s razumljivim obrazloženjem (zašto odgovara / zašto ne),
- **vodi direktno na originalni oglas** — nikad ne izmišlja oglase, plate, firme ni datume,
- radi kao **instalabilna Windows 11 aplikacija** ili kao web UI na lokalnom backendu — podaci nikad ne napuštaju računar.

Geografski prioritet (promjenjiv u pretrazi): **1. BiH → 2. Balkan → 3. Evropa → 4. svijet (uključujući remote)**. Rangiranje je po relevantnosti, ne samo po blizini.

---

## Ključne karakteristike

| Oblast | Šta radi |
|---|---|
| 🔍 Pretraga prirodnim jezikom | Izvlači zanimanje, vještine, grad, državu, platu, remote/hibrid, ugovor |
| 🏆 Rangiranje | Transparentna ocjena 0–100 s konkretnim razlozima za i protiv |
| 🌍 Filteri | Država, grad, kategorija, remote/hibrid/lokacija, ugovor, plata, datum |
| 🔌 Konektori | 10 provjerenih izvora (Klix Posao i MojPosao.ba za BiH + Greenhouse, Remotive, RemoteOK, Arbeitnow, JobTech, EURES, Posao.hr, WWR); svaki testiran uživo prije uključivanja |
| 🧹 Kvalitet podataka | Normalizacija, deduplikacija, provjera svježine; nepoznato se prikazuje kao „Nije navedeno” |
| 🤖 AI jezgro | OpenCode CLI s besplatnim modelom (bundlan u instalaciju) — **radi bez prijave i bez ključeva**; ako model nije dostupan, pretraga se iskreno nastavlja po ključnim riječima |
| 🔒 Privatnost | Nema naloga, nema CV-jeva, nema historije pretrage; sirovi upiti se ne logiraju |
| 🖥️ Dvije platforme | Web (Next.js) + Windows 11 installer (Tauri 2, .msi) na istom API-ju |
| 🛡️ Sigurnost | SSRF zaštita, rate limiting, admin token, validacija ulaza — sve testirano |

---

## Kako radi

```
┌──────────────┐      ┌──────────────┐
│  Next.js web │──────▶              │
└──────────────┘      │   FastAPI    │──▶ Store: samo memorija (bez baze, bez diska)
┌──────────────┐      │   :8010      │
│ Tauri 2 .msi │──────▶              │
│ Windows 11   │      │ konektori ▶ normalizacija ▶ dedup ▶ AI ▶ rangiranje
└──────────────┘      └──────────────┘
```

Windows instalacija je samostalna: `.msi` nosi backend (PyInstaller sidecar) i OpenCode CLI,
pa na korisničkom računaru nije potreban Python ni ručna instalacija CLI-ja.

Backend moduli (`backend/app/`): `main` (rute), `config` (env), `models` (tipovi), `security` (SSRF/rate-limit/auth), `store` (samo memorija), `normalize`, `dedup`, `criteria` (parser namjere), `ranking`, `connectors`, `ai_providers`, `admin` (skeniranje). Detalji: [`docs/ARHITEKTURA.md`](docs/ARHITEKTURA.md).

---

## Brzi start

### Preduslovi

- Python 3.12+, Node.js 22+, git. (Rust samo za lokalni Tauri build; Windows installer se pravi u CI-ju.)

### 1. Backend

```bash
cd backend
python3 -m venv venv && venv/bin/pip install -r requirements.txt
cp ../.env.example .env   # obavezno unesi jak ADMIN_TOKEN
venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8010
```

Provjera: `curl http://127.0.0.1:8010/api/health` → `{"status":"ok",...}` (bez tajni).

### 2. Probni sken (stvarni oglasi)

```bash
curl -X POST http://127.0.0.1:8010/api/admin/scan -H "X-Admin-Token: TVOJ_TOKEN"
```

### 3. Pretraga

```bash
curl -X POST http://127.0.0.1:8010/api/search \
  -H "Content-Type: application/json" \
  -d '{"upit":"Terenski komercijalist u Tešnju, plata najmanje 1800 KM"}'
```

### 4. Frontend

```bash
cd frontend && npm install && npm run dev
# otvori http://localhost:3000
# NEXT_PUBLIC_API_URL pokazuje na backend (npr. http://127.0.0.1:8010)
```

### 5. Testovi

```bash
cd backend && venv/bin/python -m pytest -q    # 28 testova
cd frontend && npm test && npm run build       # 2 testa + build
```

---

## API referenca

Sve rute vraćaju JSON; greške su strukturirane (`{"greska": "..."}`), bez stack tracea.

| Metoda | Ruta | Opis | Autorizacija |
|---|---|---|---|
| GET | `/api/health` | Stanje servisa (bez tajni) | — |
| GET | `/api/jobs?q=&drzava=&grad=&kategorija=&vrsta_rada=&stranica=&po_stranici=` | Paginirana pretraga + filteri | — (rate limit) |
| GET | `/api/jobs/{job_id}` | Detalji oglasa | — (rate limit) |
| POST | `/api/search` | `{upit, stranica?, po_stranici?, geo_prioritet?}` → kriteriji + rangirani rezultati | — (AI rate limit) |
| GET | `/api/sources` | Javni sažetak izvora | — |
| GET | `/api/sources/health` | Status izvora (bez tajni) | — |
| POST | `/api/admin/scan?izvor=` | Pokreće skeniranje | `X-Admin-Token` |
| GET | `/api/admin/status` | Status integracija | `X-Admin-Token` |

Interaktivna OpenAPI dokumentacija: `http://127.0.0.1:8010/docs`.

Primjer odgovora `/api/search` (skraćeno):

```json
{
  "kriteriji": {"zanimanje": "prodaja", "grad": "Tešanj", "plata_min": 1800.0, "plata_valuta": "BAM"},
  "ukupno": 12,
  "rezultati": [{"oglas": {...}, "ocjena": 78.5,
    "zasto_odgovara": ["Lokacija odgovara: Tešanj."],
    "zasto_ne_odgovara": ["Datum objave nije naveden."]}],
  "ai_napomena": "OpenCode CLI tumačenje + deterministička validacija."
}
```

---

## Izvori oglasa

Svaki konektor ima: timeout 12s, limit veličine odgovora, SSRF provjeru, umjereno osvježavanje (6h) i poštovanje ToS/robots. Lažni i statički konektori su zabranjeni pravilima projekta.

**Testirano uživo 2026-10-21** — svaki konektor je pojedinačno pokrenut (`skeniraj()`), pa tek onda uključen:

| Izvor | Tip | Obuhvat | Rezultat testa |
|---|---|---|---|
| `klix-posao` (Klix Posao) | javni sitemap + schema.org `JobPosting` | BiH | ✅ 60 oglasa (od 186 aktivnih u sitemapu; cap 60/sken), pun opis/plata/tip ugovora |
| `mojposao-ba` (MojPosao.ba) | javne stranice pretrage (SSR) | BiH | ✅ 100 oglasa; naslov, poslodavac, lokacija, URL |
| `greenhouse-eu` | javni boards API | Evropa + remote | ✅ 1150 oglasa |
| `remotive` | javni API | svijet-remote | ✅ 10 oglasa |
| `remoteok` | javni API | svijet-remote | ✅ 99 oglasa |
| `arbeitnow` | javni API | Evropa + remote | ✅ 300 oglasa |
| `jobtech-se` | otvoreni podaci | Švedska | ✅ 100 oglasa |
| `eures` | javni pretraživač | EU | ✅ 50 oglasa |
| `posao-hr-rss` | RSS | Hrvatska | ✅ 30 oglasa |
| `wwr-rss` | RSS | svijet-remote | ✅ 92 oglasa |

Ukupan sken svih izvora: **~1240 jedinstvenih oglasa za ~30 s** (broj varira sa izvorima) (dedup radi; pokreće se u pozadini pri startu).

### Provjereno i odbijeno (nije uključeno)

| Kandidat | Razlog |
|---|---|
| `posao.ba` | Preusmjerava na `serda.ba` — nije više job board |
| `poslovi.ba` | Oglasi se ne renderiraju u javnom HTML-u; nema provjerljivog strukturiranog endpointa |
| `zaposli.ba` | Marketplace za majstore/usluge, ne oglasi za zaposlenje |
| `boljiposao.com` | Vraća prazno tijelo ne-browser klijentima; content-signals u robots.txt |
| `job.ba` | 302 bez `Location` headera na popis oglasa — nedostupno |
| `burzarada.ba`, `uposleni.ba`, `posao-bih.com`, `oglasi.ba` | Domeni se ne resolviraju |

Napomena: dodavanje novog izvora je jedan konektor + unos u `REGISTAR`/`META_IZVORA`; bez provjerenog javnog pristupa izvor se ne uključuje.

---

## AI pretraga i rangiranje

Upit se **privremeno** analizira (nikad se ne pohranjuje): zanimanje → kategorija, grad/država, plata (KM/BAM/EUR/€/$), remote/hibrid, ugovor, vještine. Jezgro je **OpenCode CLI** (`opencode run --format json`, bez `--auto`, u praznom temp direktoriju, timeout 45 s), bundlan uz aplikaciju.

Podrazumijevani model je `opencode/deepseek-v4.1-flash-free` — besplatni OpenCode Zen model koji **radi bez prijave i bez računa** (bez `auth.json`, bez API ključa). Model se mijenja kroz `OPENCODE_MODEL` (npr. `opencode/glm-5.3-flash-free`). **Aplikacija ne posjeduje i ne traži API ključeve** — nema ih u browseru, desktop paketu, logovima ni repozitoriju. Modelov JSON je savjet koji validira deterministički parser. Ako model nije dostupan (mreža/kvota), pretraga **ne pada**: koristi lokalni parser ključnih riječi, a odgovor to jasno navodi u `ai_napomena` — nikad se ne predstavlja kao AI rezultat.

Signali rangiranja: zanimanje/vještine, lokacija, zahtjevi korisnika, tip zaposlenja, plata (ako je poznata — **oglas bez plate se ne kažnjava**), svježina. Ocjena je procjena relevantnosti, ne garancija zaposlenja. Sadržaj oglasa tretira se kao nepouzdan ulaz (prompt-injection otpornost).

---

## Privatnost

- Nema registracije, naloga, profila, CV-jeva, prijava ni historije pretrage.
- Zabranjene kolekcije (ne kreirati): `users`, `profiles`, `cvs`, `applications`, `search_history`.
- Dozvoljeno: oglasi + metapodaci izvora + operativna statistika skeniranja (bez ličnih podataka).
- Sirovi upiti: samo u memoriji zahtjeva; logira se isključivo duljina upita i broj rezultata.

---

## Sigurnost

Tajne samo iz environmenta (`.env.example` bez vrijednosti); admin rute iza `X-Admin-Token` (constant-time poređenje); rate limiting javnog API-ja i skupih AI/sken operacija; validacija i limit ulaza (upit ≤ 2000 znakova); SSRF zaštita (samo http/https, zabrana localhost/privatnih IP/metadata endpointa, allowlist + DNS provjera, limit 2MB/odgovor, timeout); restriktivni CORS; čišćenje nepouzdanog teksta oglasa; minimalne Tauri dozvole + CSP; health endpoint bez tajni i stack tracea. Testovi: `backend/tests/test_security.py` (17/17 prolazi). Više: [`docs/SIGURNOST.md`](docs/SIGURNOST.md).

---

## Anonimnost: bez perzistencije

v1 je namjerno bez baze i bez snimanja na disk: oglasi iz skeniranja žive samo u memoriji
procesa, upit se obrađuje privremeno i ne zapisuje se nigdje, a gašenjem aplikacije **svi
podaci nestaju**. Nema korisničkih kolekcija (ni `users`, `profiles`, `cvs`, `applications`,
`search_history` — ne kreirati ih), nema historije pretrage, nema tragova na disku.

---

## Windows 11 aplikacija

Tauri 2 omotač oko istog frontenda (`desktop/src-tauri/`): normalna instalacija kroz Start meni, normalna deinstalacija, razumljive poruke + dugme za ponovno povezivanje, bez ugrađenih tajni.

**Preuzimanje:** [**Releases**](https://github.com/xnet-ba/AgentMujoJob/releases) → najnoviji `v*` → preuzmi `.msi` (~139 MB). Ako release još nema, isti instalater je u artefaktu `agentmujojob-windows` zadnjeg zelenog [Windows build](https://github.com/xnet-ba/AgentMujoJob/actions/workflows/windows-build.yml) runa. Instalater nije potpisan, pa Windows može prikazati SmartScreen upozorenje (Više informacija → Ipak pokreni). Instalacija je **samostalna**: `.msi` nosi backend kao PyInstaller sidecar i OpenCode CLI, pa na korisničkom računaru nije potreban Python ni ručna instalacija CLI-ja. Backend se podiže uz aplikaciju na `127.0.0.1:8010` i gasi pri izlasku. Instalacijski `.msi` pravi GitHub Actions workflow `windows-build.yml` (windows-latest runner; potpisivanje nije podešeno — nema certifikata). Upute: [`docs/WINDOWS-BUILD.md`](docs/WINDOWS-BUILD.md).

---

## Lokalno pokretanje

Aplikacija je namijenjena isključivo lokalnom radu na Windows 11 (instalacija kroz `.msi`). Nema javne domene ni hostinga: backend sluša `127.0.0.1:8010`, frontend je statički export unutar Tauri paketa, a podaci žive samo u memoriji procesa. Za razvoj: `uvicorn app.main:app --port 8010` u `backend/` i `npm run dev` u `frontend/`.

---

## Testiranje

- Backend: `pytest` — normalizacija, dedup, parser kriterija, rangiranje, OpenCode AI, iskrena degradacija na ključne riječi kad AI nedostaje, greške izvora, neaktivni oglasi, API validacija/paginacija, rate limit, SSRF, tajne. **28/28 prolazi.**
- Frontend: `npm test` (2/2) + `npm run build` (uspješan).
- CI (GitHub Actions): `tests.yml` na svaki push + secret-scan; `windows-build.yml` ručno/na release.
- Fixture podaci su jasno označeni testni i nikad se ne prikazuju kao produkcijski oglasi.

---

## Struktura projekta

```
AgentMujoJob/
├── backend/app/        # FastAPI: main, config, models, security, store,
│                       #          normalize, dedup, criteria, ranking,
│                       #          connectors, ai_providers, admin
├── backend/tests/      # pytest (28 testova) + jasno označeni fixturei
├── frontend/           # Next.js 14 + TypeScript (bosanski UI)
├── desktop/src-tauri/  # Tauri 2 konfiguracija + bundlani sidecari (.msi)
├── docs/               # ARHITEKTURA, KONEKTORI, WINDOWS-BUILD,
│                       # SIGURNOST + index.html
├── .github/workflows/  # tests.yml, windows-build.yml
├── AGENTS.md           # pravila za buduće AI agente
└── .env.example        # prazan predložak (bez vrijednosti)
```

---

## Status i poznata ograničenja

- ✅ Backend API + web UI implementirani, testirani, rade end-to-end sa stvarnim oglasima.
- ✅ Javan GitHub repo: `https://github.com/xnet-ba/AgentMujoJob`.
- ✅ Anonimnost: nema baze ni snimanja — gašenjem appa svi podaci nestaju.
- ✅ Lokalni rad: backend `127.0.0.1:8010` + statički frontend u Tauri paketu, bez javne domene i bez hostinga.
- ✅ Windows `.msi`/`.exe`: CI (`windows-build.yml`) proizvodi artefakt sa backendom i OpenCode CLI-jem; potpisivanje nije podešeno.
- ✅ BiH izvori: **Klix Posao** (sitemap + `JobPosting`) i **MojPosao.ba** (javna pretraga) rade; ostali domaći portali provjereni i odbijeni (tabela iznad).
- ⏳ Preostalo: potpisivanje instalatera (certifikat), šira pokrivenost BiH portala gdje postoji dozvoljen pristup.
- Pravila ponašanja za agente: [`AGENTS.md`](AGENTS.md). Nema izmišljenih podataka, nema tvrdnji bez pokrenutih provjera.

---

## Doprinos

Fork → grana od `main` → backend `pytest -q` mora proći → frontend `npm test && npm run build` mora proći → bez tajni u commitovima → oglasi samo iz provjerenih izvora s URL-om. Detalji: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licenca

MIT — vidi [`LICENSE`](LICENSE).
