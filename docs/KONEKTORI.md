# Konektori

| Izvor | URL | Obuhvat | Pristup | Osvježavanje | Status |
|---|---|---|---|---|---|
| greenhouse-eu | https://boards-api.greenhouse.io | Europa + remote | javni API | 6h | **aktivan, provjeren 2026-10-14**: probni sken vratio 1102 oglasa (375 nakon dedupa), greška null |
| BiH RSS adapter | (čeka feed URL) | BiH | RSS | 6h | nije konfiguriran — DNS `www.szzks.ba` se nije razriješio iz servera; `mojposao.ba/rss` vraća 301 — treba ručna provjera ToS + tačan feed |

Pravila: timeout 12s, retry s limitom, max 2MB/odgovor, SSRF provjera, 1 zahtjev/board/sken. Greška jednog boarda ne ruši sken. Lažni/statički konektori zabranjeni.
