"""Zajednički tipovi. Nepoznato = None, prikazuje se kao 'Nije navedeno'."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

WorkType = Literal["lokacija", "hibrid", "remote", "nepoznato"]
JobStatus = Literal["aktivan", "neaktivan"]
GeoPriority = Literal["bih", "balkan", "europa", "svijet"]


class Job(BaseModel):
    id: str
    naslov: str
    poslodavac: str | None = None
    lokacija: str | None = None
    drzava: str | None = None
    opis: str | None = None
    kategorija: str | None = None
    vjestine: list[str] = Field(default_factory=list)
    vrsta_rada: WorkType = "nepoznato"
    vrsta_ugovora: str | None = None
    plata_min: float | None = None
    plata_max: float | None = None
    plata_valuta: str | None = None
    plata_procjena: bool = False  # True => plata je procijenjena, ne doslovna
    datum_objave: str | None = None
    original_url: str
    izvor: str
    prvi_put_vidjen: str = ""
    zadnji_put_vidjen: str = ""
    zadnja_provjera: str = ""
    status: JobStatus = "aktivan"


class JobSource(BaseModel):
    id: str
    naziv: str
    url: str
    obuhvat: str
    nacin_pristupa: str
    status: Literal["aktivan", "nedostupan", "nije_konfiguriran"] = "nije_konfiguriran"
    zadnji_uspjesan_pregled: str | None = None
    napomena: str | None = None


class ScanRun(BaseModel):
    id: str
    izvor: str
    pocetak: str
    kraj: str | None = None
    pronadjeno: int = 0
    dodano: int = 0
    greska: str | None = None


class Kriteriji(BaseModel):
    upit_tekst: str = ""  # čuva se samo u memoriji zahtjeva, nikad u log/store
    zanimanje: str | None = None
    vjestine: list[str] = Field(default_factory=list)
    drzava: str | None = None
    grad: str | None = None
    remote: bool | None = None
    hibrid: bool | None = None
    vrsta_ugovora: str | None = None
    plata_min: float | None = None
    plata_valuta: str | None = None
    geo_prioritet: list[GeoPriority] = Field(default_factory=lambda: ["bih", "balkan", "europa", "svijet"])


class RangiraniOglas(BaseModel):
    oglas: Job
    ocjena: float = Field(ge=0, le=100)
    zasto_odgovara: list[str] = Field(default_factory=list)
    zasto_ne_odgovara: list[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    kriteriji: Kriteriji
    ukupno: int
    rezultati: list[RangiraniOglas]
    ai_napomena: str | None = None


def sada_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
