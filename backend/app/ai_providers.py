"""AI jezgro: isključivo OpenCode CLI s besplatnim modelima. NEMA fallbacka.

Nema API ključeva, nema vanjskih AI SDK-ova, nema HTTP poziva prema AI provajderima,
nema alternativnih provajdera (uklonjeni OpenAI/Ollama/OpenRouter putevi).
Prijava se radi jednom na serveru (`opencode auth login`); aplikacija nikad ne vidi tajne.
`opencode run` se pokreće BEZ --auto (nikakva odobrenja alata), u praznom temp direktoriju,
s timeoutom. Svaki neuspjeh podiže AiNedostupan -> API vraća 503 s iskrenom porukom,
nikad tiho degradirane rezultate.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile

from .config import settings
from .criteria import parsiraj_kriterije
from .models import Kriteriji

_JSON_BLok = re.compile(r"\{.*\}", re.DOTALL)

PROMPT = (
    "Izvuci kriterije za pretragu posla iz upita ispod i odgovori ISKLJUČIVO "
    "jednim JSON objektom bez ikakvog drugog teksta, alata ili formata. "
    "Ključevi (svi opcionalni): zanimanje, grad, drzava, remote (true/false), "
    "plata_min (broj), plata_valuta (BAM/EUR/USD), vrsta_ugovora. "
    "Ne koristi nikakve alate — samo odgovori.\n\nUpit: "
)


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


def tumaci_upit(tekst: str) -> RezultatAI:
    """Jedini AI put. Baca AiNedostupan umjesto bilo kakvog fallbacka."""
    k = parsiraj_kriterije(tekst)
    binarka = shutil.which(settings.OPENCODE_BIN)
    if not binarka:
        raise AiNedostupan("OpenCode CLI nije instaliran (OPENCODE_BIN).")
    cmd = [binarka, "run", "--format", "json", "--pure"]
    if settings.OPENCODE_MODEL:
        cmd += ["-m", settings.OPENCODE_MODEL]
    cmd += [PROMPT + tekst[:1000]]
    try:
        with tempfile.TemporaryDirectory(prefix="amj-ai-") as tmp:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=settings.OPENCODE_TIMEOUT,
                               stdin=subprocess.DEVNULL, cwd=tmp)
    except Exception as e:
        raise AiNedostupan(f"OpenCode CLI se nije izvršio: {e}"[:200]) from e
    if p.returncode != 0 or not p.stdout.strip():
        raise AiNedostupan("OpenCode CLI nije vratio odgovor (provjeriti `opencode auth login`).")
    m = _JSON_BLok.search(p.stdout)
    if not m:
        raise AiNedostupan("OpenCode CLI vratio odgovor bez strukturiranih kriterija.")
    try:
        _primijeni_model(k, json.loads(m.group(0)))
    except (json.JSONDecodeError, AttributeError) as e:
        raise AiNedostupan("OpenCode CLI vratio neispravan JSON.") from e
    return RezultatAI(k, "OpenCode CLI tumačenje + deterministička validacija.", "opencode")
