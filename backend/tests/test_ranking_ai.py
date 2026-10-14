from app.ai_providers import tumaci_upit
from app.ranking import rangiraj
from app.criteria import parsiraj_kriterije
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


def test_ai_fallback_radi_bez_kljuca():
    r = tumaci_upit("posao kuhara u Sarajevu")
    assert r.provider in ("fallback", "ollama", "openai", "openrouter")
    assert r.kriteriji.grad == "Sarajevo" or r.kriteriji.drzava == "Bosna i Hercegovina"
