# Arhitektura

```
[Next.js web] ──┐
                 ├──► [FastAPI :8010] ──► [Store: Appwrite REST | JSON fallback]
[Tauri 2 .msi] ─┘         │  konektori / normalizacija / dedup / AI / rangiranje / admin
```

Moduli backend/app: main, config, models, security, store, normalize, dedup, criteria, ranking, connectors, ai_providers, admin. Web i desktop koriste isti backend; desktop ne sadrži tajne. Odluka: bez novih servisa — postojeći Appwrite (1.8.1, Docker) + Ollama na serveru se samo koriste, ne mijenjaju.
