# Arhitektura

```
[Next.js web] ──┐
                 ├──► [FastAPI :8010] ──► [Store: samo memorija — bez baze, bez diska]
[Tauri 2 .msi] ─┘         │  konektori / normalizacija / dedup / AI / rangiranje / admin
                          │  AI: OpenCode CLI (besplatni model, bez prijave) + označeni lokalni fallback
```

Moduli backend/app: main, config, models, security, store (samo memorija), normalize, dedup, criteria, ranking, connectors, ai_providers, admin. Web i desktop koriste isti backend; desktop ne sadrži tajne. v1 namjerno nema perzistenciju: gašenjem procesa nestaju oglasi, statistika i tragovi upita.

AI jezgro je **OpenCode CLI** (`opencode run --format json`, bez `--auto`, u praznom temp direktoriju, s timeoutom). Podrazumijevani model je `opencode/deepseek-v4.1-flash-free`: besplatni OpenCode Zen model koji **radi bez prijave i bez računa** (nema auth.json, nema API ključeva). Modelov JSON je savjet koji validira deterministički parser; ako CLI-model nije dostupan, API iskreno prelazi na lokalni parser ključnih riječi i to navodi u `ai_napomena`. Nema vanjskih AI SDK-ova ni HTTP poziva prema AI provajderima. Odluka: bez novih servisa i bez perzistencije u v1.
