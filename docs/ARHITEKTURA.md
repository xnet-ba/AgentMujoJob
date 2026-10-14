# Arhitektura

```
[Next.js web] ──┐
                 ├──► [FastAPI :8010] ──► [Store: samo memorija — bez baze, bez diska]
[Tauri 2 .msi] ─┘         │  konektori / normalizacija / dedup / AI / rangiranje / admin
                          │  AI jezgro: isključivo OpenCode CLI (besplatni modeli), bez fallbacka
```

Moduli backend/app: main, config, models, security, store (samo memorija), normalize, dedup, criteria, ranking, connectors, ai_providers, admin. Web i desktop koriste isti backend; desktop ne sadrži tajne. v1 namjerno nema perzistenciju: gašenjem procesa nestaju oglasi, statistika i tragovi upita.

AI jezgro je **OpenCode CLI** (`opencode run --format json`, bez `--auto`, u praznom temp direktoriju, s timeoutom): prijava se radi jednom na serveru (`opencode auth login`, besplatni modeli preko `opencode models`), aplikacija ne posjeduje i ne traži API ključeve. Modelov JSON je savjet koji validira deterministički parser; svaki neuspjeh CLI-ja vraća grešku 503 — nema fallbacka ni vanjskih AI SDK-ova ni HTTP poziva prema AI provajderima. Odluka: bez novih servisa i bez perzistencije u v1.
