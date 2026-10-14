# Sigurnost

Tajne samo env; `.env.example` prazan; admin rute iza `X-Admin-Token` (constant-time); rate limit javnog API-ja i AI/skeniranja; validacija + limit ulaza (upit ≤2000); SSRF zaštita (samo http/https, bez localhost/privatnih IP/metadata, allowlist gdje može, limit 2MB + timeout); CORS allowlist; tekst oglasa se čisti i tretira kao podaci (prompt-injection otpornost: nikad instrukcije); health bez tajni/stack tracea; Tauri minimalne capabilities + CSP. Testirano: `backend/tests/test_security.py`.
