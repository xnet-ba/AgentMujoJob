"""Modularni konektori izvora. Svaki vraća (oglasi, status_napomena). Nikad statički lažni oglasi."""
from __future__ import annotations

import html
import json
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

    def __init__(self, kid: str, naziv: str, feed_url: str, obuhvat: str, drzava: str | None = None):
        self.id = kid
        self.naziv = naziv
        self.feed_url = feed_url
        self.obuhvat = obuhvat
        self.drzava = drzava

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
                "opis": _cisti_opis(item.findtext("description"), 2000),
                "original_url": link,
                "datum_objave": (item.findtext("pubDate") or "")[:16] or None,
                "drzava": self.drzava,
            })
        return oglasi, None


def _fetch_json(url: str, dozvoljeni: set[str], max_bytes: int = MAX_URL_FETCH_BYTES) -> dict | list:
    return json.loads(_fetch(url, dozvoljeni, max_bytes).decode("utf-8", "replace"))


def _cisti_opis(s: str | None, limit: int = 3000) -> str | None:
    if not s:
        return None
    t = re.sub(r"<[^>]+>", " ", html.unescape(s))
    t = re.sub(r"\s+", " ", t).strip()
    return t[:limit] or None


def _plata_broj(v) -> float | None:
    try:
        f = float(v)
        return f if f > 0 else None
    except (TypeError, ValueError):
        return None


class RemotiveKonektor:
    """Remotive API (bez ključa; obavezan link-back + pomen izvora — UI prikazuje izvor i link)."""

    id = "remotive"
    naziv = "Remotive (remote)"
    obuhvat = "svijet-remote"

    def skeniraj(self) -> tuple[list[dict], str | None]:
        try:
            payload = _fetch_json("https://remotive.com/api/remote-jobs?limit=100", {"remotive.com"})
            jobs = payload.get("jobs", [])
        except Exception as e:
            return [], f"nedostupan: {e}"[:200]
        return [{"stabilni_id": f"remotive-{j.get('id')}", "naslov": j.get("title"),
                 "poslodavac": j.get("company_name"), "lokacija": j.get("candidate_required_location"),
                 "opis": _cisti_opis(j.get("description")), "kategorija": j.get("category"),
                 "vrsta_rada": "remote", "vrsta_ugovora": j.get("job_type"),
                 "original_url": j.get("url", ""),
                 "datum_objave": (j.get("publication_date") or "")[:10] or None} for j in jobs if j.get("url")], None


class RemoteokKonektor:
    """RemoteOK API (bez ključa; element [0] je pravna napomena — preskače se; link-back u UI-ju)."""

    id = "remoteok"
    naziv = "RemoteOK (remote)"
    obuhvat = "svijet-remote"

    def skeniraj(self) -> tuple[list[dict], str | None]:
        try:
            payload = _fetch_json("https://remoteok.com/api", {"remoteok.com"})
            items = [x for x in payload if isinstance(x, dict) and x.get("id")]
        except Exception as e:
            return [], f"nedostupan: {e}"[:200]
        out = []
        for j in items:
            tags = j.get("tags") or []
            out.append({"stabilni_id": f"rok-{j.get('id')}", "naslov": j.get("position"),
                        "poslodavac": j.get("company"), "lokacija": j.get("location") or "Remote",
                        "opis": _cisti_opis(j.get("description")),
                        "vjestine": [t for t in tags if isinstance(t, str)][:15],
                        "vrsta_rada": "remote",
                        "plata_min": _plata_broj(j.get("salary_min")), "plata_max": _plata_broj(j.get("salary_max")),
                        "plata_valuta": "USD" if _plata_broj(j.get("salary_max")) else None,
                        "original_url": j.get("url") or j.get("apply_url") or "",
                        "datum_objave": (j.get("date") or "")[:10] or None})
        return [o for o in out if o["original_url"]], None


class ArbeitnowKonektor:
    """Arbeitnow Job Board API (besplatan uz atribuciju — izvor se prikazuje u UI-ju)."""

    id = "arbeitnow"
    naziv = "Arbeitnow (EU + remote)"
    obuhvat = "Evropa + remote"

    def skeniraj(self) -> tuple[list[dict], str | None]:
        try:
            payload = _fetch_json("https://www.arbeitnow.com/api/job-board-api", {"www.arbeitnow.com"},
                                  max_bytes=4_000_000)
            items = payload.get("data", [])
        except Exception as e:
            return [], f"nedostupan: {e}"[:200]
        return [{"stabilni_id": f"arbeitnow-{j.get('slug')}", "naslov": j.get("title"),
                 "poslodavac": j.get("company_name"), "lokacija": j.get("location"),
                 "opis": _cisti_opis(j.get("description")),
                 "vrsta_rada": "remote" if j.get("remote") else "nepoznato",
                 "original_url": j.get("url", ""),
                 "datum_objave": str(j.get("created_at") or "")[:10] or None} for j in items if j.get("url")], None


class JobtechKonektor:
    """JobTech Švedska — otvoreni podaci Arbetsförmedlingen."""

    id = "jobtech-se"
    naziv = "JobTech Švedska"
    obuhvat = "Švedska"

    def skeniraj(self) -> tuple[list[dict], str | None]:
        try:
            payload = _fetch_json("https://jobsearch.api.jobtechdev.se/search?limit=100",
                                  {"jobsearch.api.jobtechdev.se"})
            hits = payload.get("hits", [])
        except Exception as e:
            return [], f"nedostupan: {e}"[:200]
        out = []
        for h in hits:
            emp = h.get("employer") or {}
            out.append({"stabilni_id": f"jobtech-{h.get('id')}", "naslov": h.get("headline"),
                        "poslodavac": emp.get("name"), "lokacija": (h.get("workplace_addresses") or [{}])[0].get("city"),
                        "drzava": "Švedska", "opis": _cisti_opis(h.get("description", {}).get("text") if isinstance(h.get("description"), dict) else h.get("description")),
                        "original_url": h.get("webpage_url", ""),
                        "datum_objave": (h.get("publication_date") or "")[:10] or None})
        return [o for o in out if o["original_url"]], None


_EURES_ZEMLJE = {"DE": "Njemačka", "AT": "Austrija", "SE": "Švedska", "NO": "Norveška", "HR": "Hrvatska",
                 "SI": "Slovenija", "RS": "Srbija", "BA": "Bosna i Hercegovina", "IT": "Italija",
                 "FR": "Francuska", "ES": "Španija", "NL": "Holandija", "PL": "Poljska", "IE": "Irska"}


class EuresKonektor:
    """EURES EU portal (javni podaci; nezvanični search endpoint — umjereno, 50 oglasa/sken)."""

    id = "eures"
    naziv = "EURES (EU)"
    obuhvat = "Evropa (31 država)"

    def skeniraj(self) -> tuple[list[dict], str | None]:
        provjeri_url("https://europa.eu/eures/api/jv-searchengine/public/jv-search/search", {"europa.eu"})
        try:
            with httpx.stream("POST", "https://europa.eu/eures/api/jv-searchengine/public/jv-search/search",
                              headers={**UA, "Content-Type": "application/json"},
                              json={"resultsPerPage": 50, "page": 1},
                              timeout=FETCH_TIMEOUT) as r:
                r.raise_for_status()
                raw = r.read()
                if len(raw) > 4_000_000:
                    raise KonektorGreska("odgovor prevelik, prekinuto")
            payload = json.loads(raw.decode("utf-8", "replace"))
        except Exception as e:
            return [], f"nedostupan: {e}"[:200]
        out = []
        for j in payload.get("jvs", []):
            loc = j.get("locationMap") or {}
            kod = next(iter(loc.keys()), "") if isinstance(loc, dict) else ""
            emp = j.get("employer") or {}
            desc = j.get("description")
            if isinstance(desc, dict):
                desc = desc.get("textLabel") or desc.get("text")
            ts = j.get("creationDate")
            datum = None
            if isinstance(ts, (int, float)) and ts > 0:
                from datetime import datetime, timezone
                datum = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            out.append({"stabilni_id": f"eures-{j.get('id')}", "naslov": j.get("title"),
                        "poslodavac": emp.get("name"), "drzava": _EURES_ZEMLJE.get(kod, kod or None),
                        "opis": _cisti_opis(desc), "original_url": f"https://eures.europa.eu/{j.get('id')}",
                        "datum_objave": datum})
        return out, None


# Registar: greenhouse (provjeren) + RSS adapteri koji se dopunjuju bez koda.
def _jobposting(html_tekst: str) -> dict | None:
    """Izvuče schema.org JobPosting iz JSON-LD bloka (Klix ga objavljuje javno)."""
    for m in re.finditer(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html_tekst, re.S):
        try:
            d = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        for k in (d if isinstance(d, list) else [d]):
            if isinstance(k, dict) and k.get("@type") == "JobPosting":
                return k
    return None


_VRSTA_UGOVORA = {"FULL_TIME": "puno radno vrijeme", "PART_TIME": "pola radnog vremena",
                  "CONTRACTOR": "ugovor", "TEMPORARY": "privremeno", "INTERN": "praksa",
                  "VOLUNTEER": "volonterski", "PER_DIEM": "po danu"}


def _klix_id(url: str) -> int:
    m = re.search(r"/(\d+)/?$", url)
    return int(m.group(1)) if m else 0


class KlixPosaoKonektor:
    """Klix Posao (BiH). Javni sitemap aktivnih oglasa + schema.org JobPosting na detalju.

    robots.txt dozvoljava sitemap i oglase (zabranjuje samo /api/ i /oglasi/ai-search).
    """

    id = "klix-posao"
    naziv = "Klix Posao (BiH)"
    obuhvat = "Bosna i Hercegovina"
    MAX_OGLASA = 100

    def skeniraj(self) -> tuple[list[dict], str | None]:
        try:
            raw = _fetch("https://posao.klix.ba/sitemaps/active_jobs.xml", {"posao.klix.ba"}, 4_000_000)
        except (KonektorGreska, ValueError) as e:
            return [], f"nedostupan: {e}"[:200]
        urls = re.findall(r"<loc>\s*(https://posao\.klix\.ba/oglasi/[^<\s]+)\s*</loc>",
                          raw.decode("utf-8", "replace"))
        urls = sorted(set(urls), key=_klix_id, reverse=True)[: self.MAX_OGLASA]
        out: list[dict] = []
        greske = 0
        for u in urls:
            try:
                b = _fetch(u, {"posao.klix.ba"}, 600_000).decode("utf-8", "replace")
            except (KonektorGreska, ValueError):
                greske += 1
                continue
            jp = _jobposting(b)
            if not jp:
                greske += 1
                continue
            mjesto = jp.get("jobLocation") if isinstance(jp.get("jobLocation"), dict) else {}
            adr = mjesto.get("address") if isinstance(mjesto.get("address"), dict) else {}
            lokacija = ", ".join(x for x in (adr.get("addressLocality"), adr.get("addressRegion")) if x) or None
            poslodavac = (jp.get("hiringOrganization") or {}).get("name") \
                if isinstance(jp.get("hiringOrganization"), dict) else None
            plata: dict = {}
            bs = jp.get("baseSalary")
            if isinstance(bs, dict):
                vrijednost = bs.get("value") if isinstance(bs.get("value"), dict) else {}
                plata = {"plata_min": _plata_broj(vrijednost.get("minValue") or vrijednost.get("value")),
                         "plata_max": _plata_broj(vrijednost.get("maxValue")),
                         "plata_valuta": bs.get("currency")}
            tip = jp.get("employmentType")
            tip = tip[0] if isinstance(tip, list) and tip else tip
            out.append({
                "stabilni_id": f"klix-{_klix_id(u)}",
                "naslov": jp.get("title"),
                "poslodavac": poslodavac,
                "lokacija": lokacija,
                "drzava": "Bosna i Hercegovina" if adr.get("addressCountry") == "BA" else None,
                "opis": _cisti_opis(jp.get("description"), 4000),
                "vrsta_rada": "remote" if (jp.get("jobLocationType") == "TELECOMMUTE"
                                           or "remote" in (lokacija or "").lower()) else "nepoznato",
                "vrsta_ugovora": _VRSTA_UGOVORA.get(str(tip), None),
                "original_url": jp.get("url") or u,
                "datum_objave": str(jp.get("datePosted") or "")[:10] or None,
                **plata,
            })
        nap = f"{greske} oglasa preskočeno" if greske else None
        return out, nap


_CARD_TITLE = re.compile(r'data-test="job-card-content-title"[^>]*>(.*?)</h3>', re.S)
_NEAKTIVNI_ALT = {"logo-site", "avatar-site", "my-paycheck-site", "ppi-site", "logo"}


class MojposaoKonektor:
    """MojPosao.ba (BiH) — server-rendered kartice pretrage; robots dozvoljava uz Crawl-delay 1.

    Kartice daju naslov, poslodavca i lokaciju; opis ostaje None (ne izmišljamo ga).
    """

    id = "mojposao-ba"
    naziv = "MojPosao.ba (BiH)"
    obuhvat = "Bosna i Hercegovina"
    URL = "https://www.mojposao.ba/pretraga-poslova"

    def skeniraj(self) -> tuple[list[dict], str | None]:
        try:
            b = _fetch(self.URL, {"www.mojposao.ba"}, 4_000_000).decode("utf-8", "replace")
        except (KonektorGreska, ValueError) as e:
            return [], f"nedostupan: {e}"[:200]
        out: list[dict] = []
        vidjeno: set[str] = set()
        for m in _CARD_TITLE.finditer(b):
            naslov = _cisti_opis(m.group(1), 200)
            if not naslov:
                continue
            pre = b[max(0, m.start() - 8000):m.start()]
            hrefs = re.findall(r'href="(/posao/[^"?#]+)', pre)
            if not hrefs:
                continue
            url = "https://www.mojposao.ba" + hrefs[-1].replace("&amp;", "&")
            if url in vidjeno:
                continue
            vidjeno.add(url)
            alts = [a.strip() for a in re.findall(r'alt="([^"]{2,80})"', pre)
                    if a.strip() not in _NEAKTIVNI_ALT]
            pos = b[m.end():m.end() + 6000]
            lm = re.search(r'info__child[^>]*>.*?<!--\[-->(.*?)<!--\]-->', pos, re.S)
            lokacija = _cisti_opis(lm.group(1), 120) if lm else None
            out.append({
                "stabilni_id": hrefs[-1],
                "naslov": naslov,
                "poslodavac": alts[-1] if alts else None,
                "lokacija": lokacija,
                "vrsta_rada": "remote" if lokacija and "remote" in lokacija.lower() else "nepoznato",
                "original_url": url,
            })
        if not out:
            return [], "stranica pretrage bez prepoznatih oglasa"
        return out, None


# Registar: greenhouse (provjeren) + RSS adapteri koji se dopunjuju bez koda.
REGISTAR: dict[str, object] = {
    # Redoslijed = redoslijed skena; brzi izvori prvi da UI dobije podatke odmah.
    "mojposao-ba": MojposaoKonektor(),
    "greenhouse-eu": GreenhouseKonektor(),
    "remotive": RemotiveKonektor(),
    "remoteok": RemoteokKonektor(),
    "arbeitnow": ArbeitnowKonektor(),
    "jobtech-se": JobtechKonektor(),
    "eures": EuresKonektor(),
    "posao-hr-rss": RssKonektor("posao-hr-rss", "Posao.hr (RSS)", "https://www.posao.hr/rss/", "Hrvatska", "Hrvatska"),
    "wwr-rss": RssKonektor("wwr-rss", "We Work Remotely (RSS)", "https://weworkremotely.com/remote-jobs.rss", "svijet", "svijet"),
    # Klix je najsporiji (do 100 detaljnih stranica) pa ide zadnji.
    "klix-posao": KlixPosaoKonektor(),
}

RSS_IZVORI = [
    # Feed URL-ovi se unose kroz env/admin kada se provjere; prazno = nije konfiguriran.
]

META_IZVORA = {
    "klix-posao": {"url": "https://posao.klix.ba", "pristup": "javni sitemap + JobPosting JSON-LD",
                   "pravila": "robots.txt dozvoljava sitemap i oglase (ne /api/); do 100 najnovijih oglasa/sken.",
                   "osvjezavanje": "svakih 6h",
                   "polja": "naslov, poslodavac, lokacija, opis, plata, tip ugovora, url, datum"},
    "mojposao-ba": {"url": "https://www.mojposao.ba/pretraga-poslova", "pristup": "javne stranice pretrage",
                    "pravila": "robots.txt dozvoljava uz Crawl-delay 1; jedan zahtjev/sken, bez opisa.",
                    "osvjezavanje": "svakih 6h", "polja": "naslov, poslodavac, lokacija, url"},
    "greenhouse-eu": {"url": "https://boards-api.greenhouse.io", "pristup": "javni API",
                      "pravila": "Poštovati ToS poslodavca; 1 zahtjev/board/sken; timeout 12s.",
                      "osvjezavanje": "svakih 6h", "polja": "naslov, poslodavac, lokacija, opis, url, datum"},
    "remotive": {"url": "https://remotive.com/api/remote-jobs", "pristup": "javni API bez ključa",
                 "pravila": "Obavezan link-back + pomen Remotivea (UI prikazuje izvor i link).",
                 "osvjezavanje": "svakih 6h", "polja": "naslov, firma, lokacija kandidata, plata (tekst), url, datum"},
    "remoteok": {"url": "https://remoteok.com/api", "pristup": "javni API bez ključa",
                 "pravila": "Obavezan link-back + pomen izvora; element [0] je pravna napomena i preskače se.",
                 "osvjezavanje": "svakih 6h", "polja": "pozicija, firma, tagovi, plata USD, url, datum"},
    "arbeitnow": {"url": "https://www.arbeitnow.com/api/job-board-api", "pristup": "besplatan API uz atribuciju",
                  "pravila": "Izvor se prikazuje u UI-ju; snapshot ~2MB, keširati.",
                  "osvjezavanje": "svakih 6h", "polja": "naslov, firma, lokacija, remote, url, datum"},
    "jobtech-se": {"url": "https://jobsearch.api.jobtechdev.se", "pristup": "otvoreni podaci",
                   "pravila": "JobTech open data; umjereno korištenje.",
                   "osvjezavanje": "svakih 6h", "polja": "naslov, poslodavac, grad, url, datum"},
    "eures": {"url": "https://europa.eu/eures/api/jv-searchengine/public/jv-search/search", "pristup": "javni podaci EU",
              "pravila": "Nezvanični endpoint — umjereno (50 oglasa/sken), uz poštovanje uslova EURES portala.",
              "osvjezavanje": "svakih 6h", "polja": "naslov, poslodavac, država, url, datum"},
    "posao-hr-rss": {"url": "https://www.posao.hr/rss/", "pristup": "javni RSS",
                     "pravila": "Redistribuciju provjeriti s operaterom.",
                     "osvjezavanje": "svakih 6h", "polja": "naslov, opis, link, datum"},
    "wwr-rss": {"url": "https://weworkremotely.com/remote-jobs.rss", "pristup": "javni RSS",
                "pravila": "Komercijalnu redistribuciju provjeriti s operaterom.",
                "osvjezavanje": "svakih 6h", "polja": "naslov, opis, link, datum"},
}
