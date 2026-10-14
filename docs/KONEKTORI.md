# Konektori

Svi endpointi verificirani živim dohvatom sa servera 2026-10-14 (HTTP 200 + parsiranje uzorka).
Pravila za sve: timeout 12s, retry s limitom, limit veličine odgovora, SSRF provjera svakog URL-a,
umjereno osvježavanje (6h), poštovanje ToS/robots. Greška jednog izvora ne ruši sken.
Lažni/statički konektori zabranjeni.

| Izvor (id) | Endpoint | Tip | Obuhvat | Probni sken | Napomena o korištenju |
|---|---|---|---|---|---|
| greenhouse-eu | `https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true` (airbnb, stripe, doist, gitlab) | API | Evropa + remote | 1103 → 375 nakon dedupa | Javni board API poslodavca; 1 zahtjev/board/sken; `content=true` ~3.4MB po boardu (limit 8MB) |
| remotive | `https://remotive.com/api/remote-jobs?limit=100` | API | svijet-remote | 16 | Bez ključa; **obavezan link-back + pomen Remotivea** (UI prikazuje izvor i link) |
| remoteok | `https://remoteok.com/api` | API | svijet-remote | 99 | Bez ključa; element `[0]` je pravna napomena i preskače se; **obavezan link-back** |
| arbeitnow | `https://www.arbeitnow.com/api/job-board-api` | API | Evropa + remote | 300 | Besplatan uz atribuciju (izvor u UI-ju); snapshot ~2.2MB |
| jobtech-se | `https://jobsearch.api.jobtechdev.se/search?limit=100` | API | Švedska | 100 | Otvoreni podaci (JobTech open data) |
| eures | `POST https://europa.eu/eures/api/jv-searchengine/public/jv-search/search` (`resultsPerPage:50`) | API | Evropa, 31 država | 50 | Javni podaci EU; nezvanični endpoint — umjereno |
| posao-hr-rss | `https://www.posao.hr/rss/` | RSS | Hrvatska | 30 | Javan feed; redistribuciju provjeriti s operaterom |
| wwr-rss | `https://weworkremotely.com/remote-jobs.rss` | RSS | svijet-remote | 88 | Javno ponuđen RSS; komercijalnu redistribuciju provjeriti |

Ukupno: **~1700 oglasa po krugu skeniranja** (prije dedupa).

## BiH — nema javnog API/RSS (provjereno negativno)

- `mojposao.ba`: `/rss` → 404; `robots.txt` Allow:/ + Crawl-delay:1 (nije feed). Nema javnog API/RSS; ToS tipično brani automatsko preuzimanje → potreban dogovor.
- `boljiposao.com`: `/rss` → 404. Nema javnog API/RSS.
- `posao.ba`: `/rss` → 404. Nema javnog API/RSS.
- FZZZ (`fzzz.ba`), ZZZRS (`zzzrs.net`), ZZZ Brčko: naslovnice rade, feedovi ne postoje (404).
- `poslovi.infostud.com` (RS): `/rss` vraća HTML, `robots.txt` brani `/search/*`.
- `moj-posao.hr`: 403 bot-zaštita — ne dirati bez dogovora.
- Lever boards: svi testirani `{company}` tokeni → 404 (firme migrirale). Ashby obrazac (`api.ashbyhq.com/posting-api/job-board/{board}`) verificiran na notion/ashby — konkretni regionalni boardovi se dodaju kad se potvrde.

Metapodaci po izvoru (URL, pristup, polja, osvježavanje): `backend/app/connectors.py` → `META_IZVORA`, javno vidljivo na `GET /api/sources`.
