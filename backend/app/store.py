"""Skladištenje isključivo u memoriji — v1 je namjerno bez perzistencije.

Nema Appwrite-a, nema snimanja na disk, nema baze. Gašenjem aplikacije svi podaci
nestaju: oglasi iz skeniranja, statistika skeniranja i (ionako nikad pohranjeni)
korisnički upiti. Upit se obrađuje privremeno i ne zapisuje se nigdje.
"""
from __future__ import annotations

import uuid

from .dedup import dedup
from .models import sada_iso


class Store:
    def __init__(self):
        self._oglasi: dict[str, dict] = {}
        self._skeniranja: list[dict] = []

    def ocisti(self) -> None:
        self._oglasi.clear()
        self._skeniranja.clear()

    def upsert(self, oglasi: list[dict]) -> tuple[int, int]:
        novi = 0
        for o in dedup(oglasi):
            if o["id"] in self._oglasi:
                staro = self._oglasi[o["id"]]
                o["prvi_put_vidjen"] = staro.get("prvi_put_vidjen", o["prvi_put_vidjen"])
                self._oglasi[o["id"]] = o
            else:
                self._oglasi[o["id"]] = o
                novi += 1
        return len(oglasi), novi

    def svi(self) -> list[dict]:
        """Svi aktivni oglasi (bez paginacije) — za rangiranje pretrage."""
        return [o for o in self._oglasi.values() if o.get("status", "aktivan") == "aktivan"]

    def listaj(self, filteri: dict | None = None, stranica: int = 1, po_stranici: int = 20) -> tuple[list[dict], int]:
        filteri = filteri or {}
        rows = self.svi()
        for klj in ("drzava", "kategorija", "vrsta_rada", "vrsta_ugovora"):
            if filteri.get(klj):
                rows = [o for o in rows if (o.get(klj) or "").lower() == filteri[klj].lower()]
        if filteri.get("grad"):
            rows = [o for o in rows if filteri["grad"].lower() in (o.get("lokacija") or "").lower()]
        if filteri.get("q"):
            q = filteri["q"].lower()
            rows = [o for o in rows if q in f"{o.get('naslov','')} {o.get('opis','')} {o.get('poslodavac','')}".lower()]
        ukupno = len(rows)
        start = (max(1, stranica) - 1) * po_stranici
        return rows[start:start + po_stranici], ukupno

    def broj_po_izvoru(self) -> dict[str, int]:
        brojevi: dict[str, int] = {}
        for o in self.svi():
            izvor = o.get("izvor") or "nepoznato"
            brojevi[izvor] = brojevi.get(izvor, 0) + 1
        return brojevi

    def detalji(self, job_id: str) -> dict | None:
        return self._oglasi.get(job_id)

    def zabiljezi_sken(self, izvor: str, pronadjeno: int, dodano: int, greska: str | None) -> dict:
        run = {"id": uuid.uuid4().hex[:12], "izvor": izvor, "pocetak": sada_iso(),
               "kraj": sada_iso(), "pronadjeno": pronadjeno, "dodano": dodano, "greska": greska}
        self._skeniranja.append(run)
        del self._skeniranja[:-200]
        return run


store = Store()
