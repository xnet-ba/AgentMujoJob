"""Modularni konektori izvora. Svaki vraća (oglasi, status_napomena). Nikad statički lažni oglasi."""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET

import httpx

from .models import sada_iso
from .security import FETCH_TIMEOUT, MAX_URL_FETCH_BYTES, provjeri_url

UA = {"User-Agent": "AgentMujoJob/1.0 (+open-source job search; contact via repo)"}


class KonektorGreska(Exception):
    pass


def _fetch(url: str, dozvoljeni: set[str] | None = None, max_bytes: int = MAX_URL_FETCH_BYTES) -> bytes:
    provjeri_url(url, dozvoljeni)
    try:
        with httpx.stream("GET", url, headers=UA, timeout=FETCH_TIMEOUT, follow_redirects=True) as r:
            r.raise_for_status()
            data = b""
            for chunk in r.iter_bytes(65536):
                data += chunk
                if len(data) > max_bytes:
                    raise KonektorGreska("odgovor prevelik, prekinuto")
            return data
    except httpx.HTTPError as e:
        raise KonektorGreska(f"HTTP greška: {e}") from e


class GreenhouseKonektor:
    """Javni Greenhouse boards API (dozvoljen javni API poslodavaca). Provjereno radi 2026-10."""

    id = "greenhouse-eu"
    naziv = "Greenhouse EU poslodavci"
    obuhvat = "Evropa + remote"
    boards = ["airbnb", "stripe", "doist", "gitlab"]

    def skeniraj(self) -> tuple[list[dict], str | None]:
        oglasi: list[dict] = []
        for board in self.boards:
            url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
            try:
                raw = _fetch(url, {"boards-api.greenhouse.io"}, max_bytes=8_000_000)
            except Exception:
                continue  # jedan board pao — ostali se i dalje čitaju
            try:
                import json
                payload = json.loads(raw.decode("utf-8", "replace"))
            except Exception:
                continue
            for j in payload.get("jobs", []):
                loc = (j.get("location") or {}).get("name", "")
                oglasi.append({
                    "stabilni_id": f"gh-{j.get('id')}",
                    "naslov": j.get("title"),
                    "poslodavac": board.title(),
                    "lokacija": loc,
                    "drzava": loc.split(",")[-1].strip() if "," in loc else loc,
                    "opis": re.sub(r"<[^>]+>", " ", html.unescape(j.get("content") or ""))[:4000],
                    "vrsta_rada": "remote" if "remote" in loc.lower() else "nepoznato",
                    "original_url": j.get("absolute_url", ""),
                    "datum_objave": (j.get("updated_at") or "")[:10] or None,
                })
        if not oglasi:
            return [], "svi boardovi nedostupni u ovom krugu"
        return oglasi, None


class RssKonektor:
    """Generički RSS adapter — URL se zadaje konfiguracijom, SSRF zaštićen."""

    def __init__(self, kid: str, naziv: str, feed_url: str, obuhvat: str):
        self.id = kid
        self.naziv = naziv
        self.feed_url = feed_url
        self.obuhvat = obuhvat

    def skeniraj(self) -> tuple[list[dict], str | None]:
        try:
            raw = _fetch(self.feed_url)
        except (KonektorGreska, ValueError) as e:
            return [], f"nedostupan: {e}"
        try:
            root = ET.fromstring(raw)
        except ET.ParseError as e:
            return [], f"neispravan RSS: {e}"
        oglasi: list[dict] = []
        for item in root.iter("item"):
            link = (item.findtext("link") or "").strip()
            if not link:
                continue
            oglasi.append({
                "naslov": item.findtext("title"),
                "opis": re.sub(r"<[^>]+>", " ", item.findtext("description") or "")[:2000],
                "original_url": link,
                "datum_objave": (item.findtext("pubDate") or "")[:16] or None,
                "drzava": "Bosna i Hercegovina",
            })
        return oglasi, None


# Registar: greenhouse (provjeren) + RSS adapteri koji se dopunjuju bez koda.
REGISTAR: dict[str, object] = {"greenhouse-eu": GreenhouseKonektor()}

RSS_IZVORI = [
    # Feed URL-ovi se unose kroz env/admin kada se provjere; prazno = nije konfiguriran.
]

META_IZVORA = {
    "greenhouse-eu": {"url": "https://boards-api.greenhouse.io", "pristup": "javni API",
                      "pravila": "Poštovati ToS poslodavca; 1 zahtjev/board/sken; timeout 12s.",
                      "osvjezavanje": "svakih 6h", "polja": "naslov, poslodavac, lokacija, opis, url, datum"},
}
