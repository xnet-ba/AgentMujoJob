"""Transparentno rangiranje — ocjena je procjena relevantnosti, ne garancija."""
from __future__ import annotations

from .models import Kriteriji

GEO_TEZINE = {"bih": 30.0, "balkan": 20.0, "europa": 10.0, "svijet": 0.0}
BALKAN = {"srbija", "hrvatska", "crna gora", "slovenija", "sjeverna makedonija", "albanija", "kosovo"}
EUROPA = {"njemačka", "austrija", "italija", "francuska", "španija", "holandija", "poljska", "češka"}


def geo_zona(drzava: str | None) -> str:
    d = (drzava or "").lower()
    if "bosna" in d or "hercegov" in d or d.strip() == "bih":
        return "bih"
    if d in BALKAN or any(b in d for b in BALKAN):
        return "balkan"
    if d in EUROPA or "europa" in d or "europe" in d:
        return "europa"
    return "svijet"


def rangiraj(oglas: dict, k: Kriteriji) -> tuple[float, list[str], list[str]]:
    bodovi = 0.0
    za: list[str] = []
    protiv: list[str] = []
    tekst = f"{oglas.get('naslov','')} {oglas.get('opis','')} {oglas.get('kategorija','')}".lower()

    if k.zanimanje and k.zanimanje in tekst:
        bodovi += 30
        za.append(f"Zanimanje odgovara kategoriji „{k.zanimanje}”.")
    elif k.zanimanje:
        protiv.append(f"Nije prepoznata kategorija „{k.zanimanje}” u oglasu.")
    if k.vjestine:
        pogodak = sum(1 for v in k.vjestine if v in tekst)
        if pogodak:
            bodovi += min(15, pogodak * 5)
            za.append(f"Pronađeno {pogodak} podudarnih vještina/pojmova.")
    if k.grad and k.grad.lower() in (oglas.get("lokacija") or "").lower():
        bodovi += 25
        za.append(f"Lokacija odgovara: {k.grad}.")
    elif k.grad:
        protiv.append(f"Oglas nije u mjestu {k.grad} — provjerite udaljenost.")
    elif k.drzava and k.drzava.lower() in (oglas.get("drzava") or "").lower():
        bodovi += 20
        za.append(f"Država odgovara: {k.drzava}.")
    zona = geo_zona(oglas.get("drzava"))
    bodovi += GEO_TEZINE.get(zona, 0) * 0.3
    if k.remote is True:
        if oglas.get("vrsta_rada") == "remote":
            bodovi += 15
            za.append("Oglas je remote.")
        else:
            protiv.append("Oglas nije označen kao remote.")
    if k.plata_min is not None:
        pmax = oglas.get("plata_max")
        pmin = oglas.get("plata_min")
        if pmax is not None and pmax >= k.plata_min:
            bodovi += 15
            za.append("Plata zadovoljava traženi minimum.")
        elif pmin is None and pmax is None:
            za.append("Plata nije navedena — oglas nije kažnjen zbog toga.")
        else:
            protiv.append("Navedena plata je ispod traženog minimuma.")
    if oglas.get("datum_objave"):
        bodovi += 5
        za.append("Oglas ima datum objave.")
    else:
        protiv.append("Datum objave nije naveden.")
    return round(min(100, bodovi), 1), za[:4], protiv[:4]
