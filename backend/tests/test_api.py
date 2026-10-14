import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.store import store
from .fixtures import TEST_OGLASI

client = TestClient(app, raise_server_exceptions=False)


def setup_function(_):
    store._write(store.jobs_path, TEST_OGLASI)


def test_health_bez_tajni():
    r = client.get("/api/health")
    assert r.status_code == 200 and "status" in r.json()
    assert "ADMIN_TOKEN" not in r.text and "API_KEY" not in r.text


def test_jobs_paginacija_i_filter():
    r = client.get("/api/jobs", params={"grad": "Tešanj"})
    assert r.json()["ukupno"] == 1
    r2 = client.get("/api/jobs", params={"stranica": 99})
    assert r2.json()["rezultati"] == []


def test_search_validacija():
    assert client.post("/api/search", json={"upit": "x"}).status_code == 422
    r = client.post("/api/search", json={"upit": "komercijalist u Tešnju plata 1800 KM"})
    assert r.status_code == 200 and r.json()["ukupno"] >= 1


def test_admin_zasticen():
    assert client.post("/api/admin/scan").status_code == 401
    assert client.get("/api/admin/status").status_code == 401


def test_neaktivan_oglas_se_ne_vraca():
    rows = [dict(TEST_OGLASI[0], status="neaktivan"), TEST_OGLASI[1]]
    store._write(store.jobs_path, rows)
    assert client.get("/api/jobs").json()["ukupno"] == 1
