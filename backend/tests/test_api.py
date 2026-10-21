import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.store import store
from .fixtures import TEST_OGLASI

client = TestClient(app, raise_server_exceptions=False)


def setup_function(_):
    store.ocisti()
    store.upsert(TEST_OGLASI)


def test_health_bez_tajni():
    r = client.get("/api/health")
    assert r.status_code == 200 and "status" in r.json()
    assert "ADMIN_TOKEN" not in r.text and "API_KEY" not in r.text


def test_jobs_paginacija_i_filter():
    r = client.get("/api/jobs", params={"grad": "Tešanj"})
    assert r.json()["ukupno"] == 1
    r2 = client.get("/api/jobs", params={"stranica": 99})
    assert r2.json()["rezultati"] == []


def test_search_validacija(monkeypatch):
    assert client.post("/api/search", json={"upit": "x"}).status_code == 422
    import app.main as m
    from app.ai_providers import RezultatAI
    from app.criteria import parsiraj_kriterije
    k = parsiraj_kriterije("komercijalist u Tešnju plata 1800 KM")
    monkeypatch.setattr(m, "tumaci_upit", lambda t: RezultatAI(k, "test", "opencode"))
    r = client.post("/api/search", json={"upit": "komercijalist u Tešnju plata 1800 KM"})
    assert r.status_code == 200 and r.json()["ukupno"] >= 1


def test_search_bez_ai_koristi_kljucne_rijeci(monkeypatch):
    import app.main as m
    from app.ai_providers import AiNedostupan

    def pad(t):
        raise AiNedostupan("test")
    monkeypatch.setattr(m, "tumaci_upit", pad)
    r = client.post("/api/search", json={"upit": "komercijalist u Tešnju"})
    assert r.status_code == 200
    d = r.json()
    assert "ključnim riječima" in (d.get("ai_napomena") or "")
    assert d["ukupno"] >= 1


def test_admin_zasticen():
    assert client.post("/api/admin/scan").status_code == 401
    assert client.get("/api/admin/status").status_code == 401


def test_neaktivan_oglas_se_ne_vraca():
    rows = [dict(TEST_OGLASI[0], status="neaktivan"), TEST_OGLASI[1]]
    store.ocisti()
    store.upsert(rows)
    assert client.get("/api/jobs").json()["ukupno"] == 1
