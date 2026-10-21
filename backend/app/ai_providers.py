"""AI jezgro: isključivo OpenCode CLI s besplatnim modelima. NEMA fallbacka.

Nema API ključeva, nema vanjskih AI SDK-ova, nema HTTP poziva prema AI provajderima,
nema alternativnih provajdera (uklonjeni OpenAI/Ollama/OpenRouter putevi).
`opencode/<model>-free` modeli rade bez prijave i bez računa — nema auth.json ni ključeva;
aplikacija nikad ne vidi tajne. Model se može promijeniti kroz OPENCODE_MODEL.
`opencode run` se pokreće BEZ --auto (nikakva odobrenja alata), u praznom temp direktoriju,
s timeoutom. Svaki neuspjeh podiže AiNedostupan -> API vraća 503 s iskrenom porukom,
nikad tiho degradirane rezultate.
"""
from __future__ import annotations

import json
import re
import shutil
import time
import subprocess
import tempfile

from .config import settings
from .criteria import parsiraj_kriterije
from .models import Kriteriji

_JSON_BLok = re.compile(r"\{[^{}]*\}")

POZNATI_KLJUCEVI = {"zanimanje", "grad", "drzava", "remote", "plata_min", "plata_valuta", "vrsta_ugovora"}

PROMPT = (
    "Tvoj jedini zadatak: iz upita ispod izvuci kriterije za pretragu posla. "
    "Ne pretražuj ništa, ne pozivaj alate, ne izvršavaj komande, ne objašnjavaj. "
    "Odgovori ISKLJUČIVO jednim JSON objektom, bez ikakvog drugog teksta. "
    "Ključevi (svi opcionalni): zanimanje, grad, drzava, remote (true/false), "
    "plata_min (broj), plata_valuta (BAM/EUR/USD), vrsta_ugovora.\n\nUpit: "
)


def _izvuci_tekst_iz_eventa(stdout: str) -> str:
    """`opencode run --format json` vraća JSON evente po linijama; tekst je u text poljima."""
    dijelovi: list[str] = []

    def _hodaj(o) -> None:
        if isinstance(o, dict):
            t = o.get("text")
            if isinstance(t, str):
                dijelovi.append(t)
            for v in o.values():
                _hodaj(v)
        elif isinstance(o, list):
            for v in o:
                _hodaj(v)

    for lin in stdout.splitlines():
        lin = lin.strip()
        if not lin.startswith("{"):
            if lin:
                dijelovi.append(lin)
            continue
        try:
            _hodaj(json.loads(lin))
        except json.JSONDecodeError:
            continue
    return "".join(dijelovi)


def _izvuci_kriterije_json(tekst: str) -> dict:
    """Zadnji parsabilni JSON blok s poznatim ključevima — modelov savjet, ne istina."""
    for m in reversed(list(_JSON_BLok.finditer(tekst))):
        try:
            podaci = json.loads(m.group(0))
        except json.JSONDecodeError:
            continue
        if isinstance(podaci, dict) and POZNATI_KLJUCEVI & set(podaci.keys()):
            return podaci
    raise AiNedostupan("OpenCode CLI vratio odgovor bez strukturiranih kriterija.")


class AiNedostupan(Exception):
    """OpenCode CLI nije uspio — pozivalac vraća 503, bez fallbacka."""


class RezultatAI:
    def __init__(self, kriteriji: Kriteriji, napomena: str | None, provider: str):
        self.kriteriji = kriteriji
        self.napomena = napomena
        self.provider = provider


def _primijeni_model(k: Kriteriji, podaci: dict) -> None:
    """Modelov JSON je savjet; deterministički parser ostaje osnova — preuzimaju se samo validna polja."""
    if isinstance(podaci.get("zanimanje"), str) and podaci["zanimanje"].strip():
        k.zanimanje = podaci["zanimanje"].strip()[:60]
    if isinstance(podaci.get("grad"), str) and podaci["grad"].strip():
        k.grad = podaci["grad"].strip()[:60]
        if not k.drzava and isinstance(podaci.get("drzava"), str):
            k.drzava = podaci["drzava"].strip()[:60]
    elif isinstance(podaci.get("drzava"), str) and podaci["drzava"].strip():
        k.drzava = podaci["drzava"].strip()[:60]
    if isinstance(podaci.get("remote"), bool):
        k.remote = podaci["remote"]
    try:
        if podaci.get("plata_min") is not None and float(podaci["plata_min"]) > 0:
            k.plata_min = float(podaci["plata_min"])
            if podaci.get("plata_valuta") in ("BAM", "EUR", "USD"):
                k.plata_valuta = podaci["plata_valuta"]
    except (TypeError, ValueError):
        pass
    if isinstance(podaci.get("vrsta_ugovora"), str) and podaci["vrsta_ugovora"].strip():
        k.vrsta_ugovora = podaci["vrsta_ugovora"].strip()[:40]


def _pokreni_cli(cmd: list[str]):
    with tempfile.TemporaryDirectory(prefix="amj-ai-") as tmp:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=settings.OPENCODE_TIMEOUT,
                              stdin=subprocess.DEVNULL, cwd=tmp)


def tumaci_upit(tekst: str) -> RezultatAI:
    """Jedini AI put. Baca AiNedostupan umjesto bilo kakvog fallbacka.

    Besplatni modeli su povremeno nedostupni; jedan brzi ponovni pokušaj pokriva
    taj slučaj, a poruka nikad ne sadrži putanje ni internu komandu (ide u UI).
    """
    k = parsiraj_kriterije(tekst)
    binarka = shutil.which(settings.OPENCODE_BIN)
    if not binarka:
        raise AiNedostupan("AI model nije dostupan (OpenCode CLI nije pronađen).")
    cmd = [binarka, "run", "--format", "json", "--pure"]
    if settings.OPENCODE_MODEL:
        cmd += ["-m", settings.OPENCODE_MODEL]
    cmd += [PROMPT + tekst[:1000]]

    razlog = "model nije odgovorio"
    for _ in range(2):
        pocetak = time.monotonic()
        try:
            p = _pokreni_cli(cmd)
        except subprocess.TimeoutExpired:
            razlog = "model nije odgovorio u roku"
            break
        except OSError:
            razlog = "model se nije mogao pokrenuti"
            break
        if p.returncode == 0 and p.stdout.strip():
            _primijeni_model(k, _izvuci_kriterije_json(_izvuci_tekst_iz_eventa(p.stdout)))
            return RezultatAI(k, "OpenCode CLI tumačenje + deterministička validacija.", "opencode")
        razlog = "model je vratio prazan odgovor"
        if time.monotonic() - pocetak > 15:
            break  # spor neuspjeh: ponovni pokušaj bi samo udvostručio čekanje
    raise AiNedostupan(razlog)
