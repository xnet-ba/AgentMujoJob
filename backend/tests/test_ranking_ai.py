"""Testovi jedinog AI puta (OpenCode CLI). Nema fallbacka — neuspjeh baca AiNedostupan."""
import pytest

import app.ai_providers as ap
from app.ai_providers import AiNedostupan, tumaci_upit
from app.criteria import parsiraj_kriterije
from app.ranking import rangiraj
from .fixtures import TEST_OGLASI


def test_rangiranje_lokacija_pobjedjuje():
    k = parsiraj_kriterije("komercijalist Tešanj plata 1800 KM")
    o1, _z, _p = rangiraj(TEST_OGLASI[0], k)
    o2, _z2, _p2 = rangiraj(TEST_OGLASI[1], k)
    assert o1 > o2


def test_rangiranje_ne_kaznjava_platu_koje_nema():
    k = parsiraj_kriterije("python remote plata 5000 EUR")
    ocjena, za, protiv = rangiraj(TEST_OGLASI[1], k)
    assert ocjena > 0 and any("remote" in z.lower() for z in za)


def test_ai_bez_cli_baca():
    import shutil
    orig = shutil.which
    shutil.which = lambda *a, **k: None
    try:
        with pytest.raises(AiNedostupan):
            tumaci_upit("posao kuhara u Sarajevu")
    finally:
        shutil.which = orig


def _event_sa_tekstom(tekst: str) -> str:
    import json as _j
    return _j.dumps({"type": "text", "part": {"type": "text", "text": tekst}})


def test_ai_opencode_json_spaja_s_parserom(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda *a, **k: "/usr/bin/opencode")

    class P:
        returncode = 0
        stdout = _event_sa_tekstom('neki tekst {"grad": "Mostar", "plata_min": 2000, "plata_valuta": "BAM"} kraj')

    monkeypatch.setattr(ap.subprocess, "run", lambda *a, **k: P())
    r = tumaci_upit("posao u Mostaru plata 2000 KM")
    assert r.provider == "opencode"
    assert r.kriteriji.grad == "Mostar" and r.kriteriji.plata_min == 2000.0


def test_ai_pad_cli_baca_bez_fallbacka(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda *a, **k: "/usr/bin/opencode")
    monkeypatch.setattr(ap.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(OSError("pad")))
    with pytest.raises(AiNedostupan):
        tumaci_upit("posao kuhara u Sarajevu")


def test_ai_los_json_baca(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda *a, **k: "/usr/bin/opencode")

    class P:
        returncode = 0
        stdout = _event_sa_tekstom("samo tekst bez ikakvog jsona")

    monkeypatch.setattr(ap.subprocess, "run", lambda *a, **k: P())
    with pytest.raises(AiNedostupan):
        tumaci_upit("posao kuhara u Sarajevu")
