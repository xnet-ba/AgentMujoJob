"""Determinističko parsiranje kriterija iz prirodnog jezika (radi i bez AI ključa)."""
from __future__ import annotations

import re

from .models import Kriteriji

GRADOVI_BIH = ["sarajevo", "sarajevu", "banja luka", "banjaluka", "banjaluci", "tuzla", "tuzli",
               "zenica", "zenici", "mostar", "mostaru", "tesanj", "tešanj", "tesnju", "tešnju",
               "bihac", "bihać", "bihacu", "bihaću", "brcko", "brčko", "brckom", "brčkom",
               "prijedor", "prijedoru", "doboj", "doboju", "bijeljina", "bijeljini",
               "travnik", "travniku", "cazin", "cazinu"]
GRAD_NORM = {"sarajevu": "Sarajevo", "banjaluci": "Banja Luka", "banjaluka": "Banja Luka",
             "tuzli": "Tuzla", "zenici": "Zenica", "mostaru": "Mostar", "tesnju": "Tešanj",
             "tešnju": "Tešanj", "tesanj": "Tešanj", "tešanj": "Tešanj", "bihacu": "Bihać",
             "bihaću": "Bihać", "brckom": "Brčko", "brčkom": "Brčko", "brcko": "Brčko",
             "brčko": "Brčko", "prijedoru": "Prijedor", "doboju": "Doboj",
             "bijeljini": "Bijeljina", "travniku": "Travnik", "cazinu": "Cazin"}
DRZAVE = {"bosna": "Bosna i Hercegovina", "bih": "Bosna i Hercegovina", "hercegovina": "Bosna i Hercegovina",
          "srbija": "Srbija", "srbiji": "Srbija", "hrvatska": "Hrvatska", "hrvatskoj": "Hrvatska",
          "crna gora": "Crna Gora", "slovenija": "Slovenija", "sloveniji": "Slovenija",
          "makedonija": "Sjeverna Makedonija", "albanija": "Albanija", "kosovo": "Kosovo",
          "njemacka": "Njemačka", "njemačka": "Njemačka", "njemačkoj": "Njemačka",
          "austrija": "Austrija", "austriji": "Austrija"}
KATEGORIJE = {"komercijalist": "prodaja", "prodaj": "prodaja", "vozac": "transport", "vozač": "transport",
              "kuhar": "ugostiteljstvo", "konobar": "ugostiteljstvo", "programer": "it",
              "developer": "it", "inzenjer": "it", "inženjer": "it", "medicinsk": "zdravstvo",
              "njegovatelj": "zdravstvo", "ucitelj": "obrazovanje", "učitelj": "obrazovanje",
              "racunovo": "finansije", "računovo": "finansije", "knjigovo": "finansije",
              "mehanicar": "proizvodnja", "mehaničar": "proizvodnja", "elektricar": "proizvodnja",
              "električar": "proizvodnja", "građevin": "građevinarstvo", "gradevin": "građevinarstvo"}
PLATA_RE = re.compile(r"(\d[\d\s\.\,]*)\s*(km|bam|eur|€|\$)", re.IGNORECASE)


def parsiraj_kriterije(tekst: str) -> Kriteriji:
    t = (tekst or "").lower()
    k = Kriteriji()
    for g in GRADOVI_BIH:
        if g in t:
            k.grad = GRAD_NORM.get(g, g.title().replace("Tesanj", "Tešanj"))
            k.drzava = "Bosna i Hercegovina"
            break
    if not k.drzava:
        for frag, puno in DRZAVE.items():
            if frag in t:
                k.drzava = puno
                break
    if any(w in t for w in ("remote", "rad na daljinu", "na daljinu", "od kuće", "od kuce")):
        k.remote = True
    if "hibrid" in t:
        k.hibrid = True
    if any(w in t for w in ("neodređeno", "neodredjeno", "stalni radni odnos")):
        k.vrsta_ugovora = "neodređeno"
    elif any(w in t for w in ("određeno", "odredjeno", "honorar", "ugovor o djelu")):
        k.vrsta_ugovora = "određeno"
    m = PLATA_RE.search(t)
    if m:
        iznos = float(m.group(1).replace(" ", "").replace(".", "").replace(",", "."))
        valuta = m.group(2).upper().replace("KM", "BAM").replace("€", "EUR")
        k.plata_min = iznos
        k.plata_valuta = "BAM" if valuta == "BAM" else ("EUR" if valuta == "EUR" else valuta)
    for frag, kat in KATEGORIJE.items():
        if frag in t:
            k.zanimanje = kat
            break
    # vještine: riječi duže od 3 slova koje nisu stop-riječi (gruba heuristika)
    stop = {"tražim", "trazim", "posao", "koji", "koja", "gdje", "mogu", "moguće", "moguce",
            "putovati", "okolini", "ili", "najmanje", "plata", "radim", "raditi", "iskustvo"}
    rijeci = [w.strip(".,;:!?()") for w in t.split() if len(w) > 3]
    k.vjestine = [w for w in rijeci if w not in stop][:10]
    return k
