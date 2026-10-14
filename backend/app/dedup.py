"""Deduplikacija: stabilni ID > normalizirani URL > naslov+poslodavac+lokacija."""
from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse

_WS = re.compile(r"\s+")


def _n(s: str | None) -> str:
    return _WS.sub(" ", (s or "").lower()).strip()


def norm_url(url: str) -> str:
    u = urlparse(url.strip())
    # skini tracking parametre, fragment
    return urlunparse((u.scheme.lower(), u.netloc.lower(), u.path.rstrip("/"), "", "", ""))


def kljuc(naslov: str | None, poslodavac: str | None, lokacija: str | None) -> str:
    return f"{_n(naslov)}|{_n(poslodavac)}|{_n(lokacija)}"


def dedup(oglasi: list[dict]) -> list[dict]:
    """Spaja duplikate; različite pozicije istog poslodavca se NE spajaju (naslov je dio ključa)."""
    vidjeni_id: set[str] = set()
    vidjeni_url: set[str] = set()
    vidjeni_kljuc: set[str] = set()
    out: list[dict] = []
    for o in oglasi:
        sid = o.get("id")
        if sid and sid in vidjeni_id:
            continue
        try:
            u = norm_url(o.get("original_url", ""))
        except Exception:
            continue
        k = kljuc(o.get("naslov"), o.get("poslodavac"), o.get("lokacija"))
        if u in vidjeni_url or k in vidjeni_kljuc:
            continue
        if sid:
            vidjeni_id.add(sid)
        vidjeni_url.add(u)
        vidjeni_kljuc.add(k)
        out.append(o)
    return out
