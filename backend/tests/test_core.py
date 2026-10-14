from app.criteria import parsiraj_kriterije
from app.dedup import dedup, norm_url
from app.normalize import normaliziraj


def test_normalizacija_ne_izmislja():
    j = normaliziraj({"naslov": "  Kuhar ", "original_url": "https://x.test/1"}, "test")
    assert j.naslov == "Kuhar"
    assert j.plata_min is None and j.poslodavac is None and j.vrsta_rada == "nepoznato"


def test_normalizacija_bez_url_odbacuje():
    try:
        normaliziraj({"naslov": "x"}, "test")
        assert False
    except ValueError:
        pass


def test_dedup_spaja_iste():
    a = {"id": "a", "naslov": "Kuhar", "poslodavac": "H", "lokacija": "SA", "original_url": "https://x.test/1?a=1"}
    b = {"id": "b", "naslov": "kuhar ", "poslodavac": "h", "lokacija": "sa", "original_url": "https://x.test/1"}
    assert len(dedup([a, b])) == 1


def test_dedup_ne_spaja_razlicite_pozicije():
    a = {"naslov": "Kuhar", "poslodavac": "H", "lokacija": "SA", "original_url": "https://x.test/1"}
    b = {"naslov": "Konobar", "poslodavac": "H", "lokacija": "SA", "original_url": "https://x.test/2"}
    assert len(dedup([a, b])) == 2


def test_kriteriji_komercijalist_tesanj():
    k = parsiraj_kriterije("Tražim posao terenskog komercijaliste u Tešnju, plata najmanje 1.800 KM, mogu putovati.")
    assert k.grad == "Tešanj" and k.drzava == "Bosna i Hercegovina"
    assert k.plata_min == 1800.0 and k.plata_valuta == "BAM"
    assert k.zanimanje == "prodaja"
