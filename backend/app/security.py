"""Sigurnost: SSRF zaštita, rate limit, admin auth. Bez vanjskih zavisnosti."""
from __future__ import annotations

import hmac
import ipaddress
import socket
import time
from collections import defaultdict
from urllib.parse import urlparse

MAX_URL_FETCH_BYTES = 2_000_000
FETCH_TIMEOUT = 12

_BLOCKED_HOSTS = {"localhost", "metadata.google.internal"}
_METADATA_IPS = (ipaddress.ip_network("169.254.0.0/16"),)


def je_zabranjen_host(host: str) -> bool:
    h = (host or "").lower().strip().strip(".")
    if not h or h in _BLOCKED_HOSTS:
        return True
    if h in ("localhost",) or h.endswith(".localhost") or h.endswith(".internal") or h.endswith(".local"):
        return True
    return False


def provjeri_url(url: str, dozvoljeni_hostovi: set[str] | None = None) -> str:
    """Validira URL prije fetcha. Vraća normalizirani URL ili baca ValueError."""
    u = urlparse(url)
    if u.scheme not in ("http", "https"):
        raise ValueError("dozvoljeni su samo http/https URL-ovi")
    if not u.hostname or je_zabranjen_host(u.hostname):
        raise ValueError("zabranjen host")
    if dozvoljeni_hostovi and u.hostname.lower() not in dozvoljeni_hostovi:
        raise ValueError("host nije na listi dozvoljenih")
    try:
        infos = socket.getaddrinfo(u.hostname, None, family=socket.AF_UNSPEC)
    except socket.gaierror:
        raise ValueError("DNS razrješenje neuspješno")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            raise ValueError("privatna/rezervirana IP adresa je zabranjena")
        if any(ip in net for net in _METADATA_IPS):
            raise ValueError("cloud metadata endpoint je zabranjen")
    return url


class RateLimiter:
    """Klizni prozor u memoriji. Dovoljno za jedan proces (ponytail: redis ako bude više instanci)."""

    def __init__(self, po_minuti: int):
        self.po_minuti = po_minuti
        self._hits: dict[str, list[float]] = defaultdict(list)

    def dozvoli(self, kljuc: str) -> bool:
        sada = time.monotonic()
        prozor = [t for t in self._hits[kljuc] if sada - t < 60]
        self._hits[kljuc] = prozor
        if len(prozor) >= self.po_minuti:
            return False
        prozor.append(sada)
        return True


def provjeri_admin(primljeni: str, ocekivani: str) -> bool:
    if not ocekivani or not primljeni:
        return False
    return hmac.compare_digest(primljeni, ocekivani)


def ocisti_tekst(s: str | None, limit: int = 5000) -> str | None:
    """Skida kontrolne znakove iz nepouzdanog teksta oglasa (XSS/injection higijena)."""
    if s is None:
        return None
    c = "".join(ch for ch in s if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    return c[:limit]
