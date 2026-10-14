"""Fixture oglasi — JASNO OZNAČENI TESTNI PODACI, nikad produkcijski oglasi."""
from __future__ import annotations

TEST_OGLASI = [
    {"id": "test-1", "naslov": "Terenski komercijalist", "poslodavac": "Test d.o.o.",
     "lokacija": "Tešanj", "drzava": "Bosna i Hercegovina", "opis": "Prodaja na terenu, vozačka dozvola B.",
     "kategorija": "prodaja", "vjestine": ["prodaja", "vožnja"], "vrsta_rada": "lokacija",
     "plata_min": 1800.0, "plata_max": 2200.0, "plata_valuta": "BAM",
     "original_url": "https://primjer.test/oglasi/1", "izvor": "test",
     "prvi_put_vidjen": "2026-01-01T00:00:00Z", "zadnji_put_vidjen": "2026-01-01T00:00:00Z",
     "zadnja_provjera": "2026-01-01T00:00:00Z", "status": "aktivan"},
    {"id": "test-2", "naslov": "Python developer (remote)", "poslodavac": "Remote Test Inc",
     "lokacija": "Remote", "drzava": "Njemačka", "opis": "Python, FastAPI, remote rad.",
     "kategorija": "it", "vjestine": ["python", "fastapi"], "vrsta_rada": "remote",
     "original_url": "https://primjer.test/oglasi/2", "izvor": "test",
     "prvi_put_vidjen": "2026-01-01T00:00:00Z", "zadnji_put_vidjen": "2026-01-01T00:00:00Z",
     "zadnja_provjera": "2026-01-01T00:00:00Z", "status": "aktivan"},
]
