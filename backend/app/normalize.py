"""Normalizacija sirovih oglasa u Job. Ništa se ne izmišlja — nepoznato ostaje None."""
from __future__ import annotations

import hashlib
import re

from .models import Job, sada_iso
from .security import ocisti_tekst

_WS = re.compile(r"\s+")


def _norm_tekst(s: str | None) -> str | None:
    if s is None:
        return None
    s = _WS.sub(" ", ocisti_tekst(s, 8000) or "").strip()
    return s or None


def stabilan_id(izvor: str, stabilni: str | None, url: str) -> str:
    baza = stabilni or url
    h = hashlib.sha256(f"{izvor}|{baza}".encode()).hexdigest()[:16]
    return f"{izvor}-{h}"


def normaliziraj(sirovi: dict, izvor: str, sada: str | None = None) -> Job:
    ts = sada or sada_iso()
    url = (sirovi.get("original_url") or sirovi.get("url") or "").strip()
    if not url:
        raise ValueError("oglas bez URL-a se odbacuje")
    vrsta = (sirovi.get("vrsta_rada") or "nepoznato").lower()
    if vrsta not in ("lokacija", "hibrid", "remote", "nepoznato"):
        vrsta = "nepoznato"  # type: ignore[assignment]
    vjestine = sirovi.get("vjestine") or sirovi.get("skills") or []
    return Job(
        id=stabilan_id(izvor, sirovi.get("stabilni_id"), url),
        naslov=_norm_tekst(sirovi.get("naslov") or sirovi.get("title")) or "Nije navedeno",
        poslodavac=_norm_tekst(sirovi.get("poslodavac") or sirovi.get("company")),
        lokacija=_norm_tekst(sirovi.get("lokacija") or sirovi.get("location")),
        drzava=_norm_tekst(sirovi.get("drzava") or sirovi.get("country")),
        opis=_norm_tekst(sirovi.get("opis") or sirovi.get("description")),
        kategorija=_norm_tekst(sirovi.get("kategorija") or sirovi.get("category")),
        vjestine=[v.strip() for v in vjestine if isinstance(v, str) and v.strip()][:30],
        vrsta_rada=vrsta,  # type: ignore[arg-type]
        vrsta_ugovora=_norm_tekst(sirovi.get("vrsta_ugovora") or sirovi.get("contract")),
        plata_min=sirovi.get("plata_min"),
        plata_max=sirovi.get("plata_max"),
        plata_valuta=_norm_tekst(sirovi.get("plata_valuta") or sirovi.get("currency")),
        plata_procjena=bool(sirovi.get("plata_procjena", False)),
        datum_objave=sirovi.get("datum_objave") or sirovi.get("posted_at"),
        original_url=url,
        izvor=izvor,
        prvi_put_vidjen=sirovi.get("prvi_put_vidjen") or ts,
        zadnji_put_vidjen=ts,
        zadnja_provjera=ts,
        status="aktivan",
    )
