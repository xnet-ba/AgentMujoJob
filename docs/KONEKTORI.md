# Konektori

Svi endpointi verificirani živim dohvatom sa servera **2026-10-21** (HTTP 200 + parsiranje uzorka + pokrenut `skeniraj()`).
Pravila za sve: timeout 12s, retry s limitom, limit veličine odgovora, SSRF provjera svakog URL-a,
umjereno osvježavanje (6h), poštovanje ToS/robots. Greška jednog izvora ne ruši sken.
Lažni/statički konektori zabranjeni.

| Izvor (id) | Endpoint | Tip | Obuhvat | Probni sken | Napomena o korištenju |
|---|---|---|---|---|---|
| **klix-posao** | `https://posao.klix.ba/sitemap/active_jobs.xml` → detalj oglasa | sitemap + JSON-LD | **BiH** | 60 (cap; sitemap 186) | robots.txt dozvoljava sitemap i oglase (ne `/api/`); schema.org `JobPosting` daje naslov, opis, platu, tip ugovora, datum |
| **mojposao-ba** | `https://www.mojposao.ba/pretraga-poslova` | SSR HTML | **BiH** | 100 | robots.txt `Allow: /` + `Crawl-delay: 1`; jedan zahtjev/sken; kartice daju naslov, poslodavca, lokaciju, URL (bez opisa) |
| greenhouse-eu | `https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true` (airbnb, stripe, doist, gitlab) | API | Evropa + remote | 1150 | Javni board API poslodavca; 1 zahtjev/board/sken; `content=true` ~3.4MB po boardu (limit 8MB) |
| remotive | `https://remotive.com/api/remote-jobs?limit=100` | API | svijet-remote | 10 | Bez ključa; **obavezan link-back + pomen Remotivea** (UI prikazuje izvor i link) |
| remoteok | `https://remoteok.com/api` | API | svijet-remote | 99 | Bez ključa; element `[0]` je pravna napomena i preskače se; **obavezan link-back** |
| arbeitnow | `https://www.arbeitnow.com/api/job-board-api` | API | Evropa + remote | 300 | Besplatan uz atribuciju (izvor u UI-ju); snapshot ~2.2MB |
| jobtech-se | `https://jobsearch.api.jobtechdev.se/search?limit=100` | API | Švedska | 100 | Otvoreni podaci (JobTech open data) |
| eures | `POST https://europa.eu/eures/api/jv-searchengine/public/jv-search/search` (`resultsPerPage:50`) | API | Evropa, 31 država | 50 | Javni podaci EU; nezvanični endpoint — umjereno |
| posao-hr-rss | `https://www.posao.hr/rss/` | RSS | Hrvatska | 30 | Javan feed; redistribuciju provjeriti s operaterom |
| wwr-rss | `https://weworkremotely.com/remote-jobs.rss` | RSS | svijet-remote | 92 | Javno ponuđen RSS; komercijalnu redistribuciju provjeriti |

Ukupno: **~1.200–2.000 jedinstvenih oglasa** po krugu skeniranja (~15–40 s, dedup uključen; broj varira sa izvorima).

## BiH — provjereno 2026-10-21

Uključeno: **Klix Posao** (sitemap + `JobPosting`) i **MojPosao.ba** (javna SSR pretraga).

Odbijeno, s razlogom:

- `posao.ba` — preusmjerava na `serda.ba`, nije job board.
- `poslovi.ba` — oglasi se ne renderiraju u javnom HTML-u; nema strukturiranog endpointa.
- `zaposli.ba` — marketplace za majstore/usluge, ne oglasi za zaposlenje.
- `boljiposao.com` — prazno tijelo ne-browser klijentima; content-signals u robots.txt.
- `job.ba` — 302 bez `Location` headera na popis oglasa.
- `burzarada.ba`, `uposleni.ba`, `posao-bih.com`, `oglasi.ba` — domeni se ne resolviraju.
- FZZZ (`fzzz.ba`), ZZZRS (`zzzrs.net`), ZZZ Brčko — portali/vijesti, bez feeda oglasa.
- `poslovi.infostud.com` (RS) — `/rss` vraća HTML, robots brani `/search/*`.
- `moj-posao.hr` — 403 bot-zaštita.
- Lever/Ashby boardovi — obrazac radi, ali konkretni regionalni boardovi nisu potvrđeni.

Metapodaci po izvoru (URL, pristup, polja, osvježavanje): `backend/app/connectors.py` → `META_IZVORA`, javno vidljivo na `GET /api/sources`.
