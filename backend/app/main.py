"""AgentMujoJob backend API. Sirovi upiti se ne logiraju — samo duljina i broj rezultata."""
from __future__ import annotations

import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import admin, connectors
from .ai_providers import AiNedostupan, RezultatAI, tumaci_upit
from .config import settings
from .criteria import parsiraj_kriterije
from .models import Kriteriji, RangiraniOglas, SearchResponse
from .ranking import rangiraj
from .security import RateLimiter, provjeri_admin
from .store import store

@asynccontextmanager
async def _zivotni_ciklus(_app: FastAPI):
    # Desktop korisnik nema admin token: prvi sken konektora ide u pozadini.
    threading.Thread(target=admin.pokreni_sken, name="pocetni-sken", daemon=True).start()
    yield


app = FastAPI(title="AgentMujoJob API", version="1.0.0",
              description="Open-source AI asistent za pronalazak posla (BiH, Balkan, Europa, svijet).",
              lifespan=_zivotni_ciklus)

app.add_middleware(CORSMiddleware,
                   allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-Admin-Token"])

api_limiter = RateLimiter(settings.RATE_LIMIT_PER_MIN)
ai_limiter = RateLimiter(settings.AI_RATE_LIMIT_PER_MIN)


def _limit(limiter: RateLimiter, kljuc: str, poruka: str):
    if not limiter.dozvoli(kljuc):
        raise HTTPException(429, poruka)


class SearchIn(BaseModel):
    upit: str = Field(min_length=2, max_length=2000)
    stranica: int = Field(default=1, ge=1, le=100)
    po_stranici: int = Field(default=20, ge=1, le=50)
    geo_prioritet: list[str] | None = None


@app.get("/api/health")
def health():
    _, ukupno = store.listaj(None, 1, 1)
    return {"status": "ok", "servis": settings.APP_NAME, "perzistencija": "nema (samo memorija)",
            "spremno": ukupno > 0, "oglasa": ukupno}


@app.get("/api/jobs")
def lista_oglasa(request: Request, q: str | None = Query(default=None, max_length=200),
                 drzava: str | None = None, grad: str | None = None, kategorija: str | None = None,
                 vrsta_rada: str | None = None, stranica: int = Query(1, ge=1), po_stranici: int = Query(20, ge=1, le=50)):
    _limit(api_limiter, request.client.host if request.client else "x", "Previše zahtjeva, pokušajte kasnije.")
    rows, ukupno = store.listaj({"q": q, "drzava": drzava, "grad": grad, "kategorija": kategorija,
                                 "vrsta_rada": vrsta_rada}, stranica, po_stranici)
    return {"ukupno": ukupno, "stranica": stranica, "rezultati": rows}


@app.get("/api/jobs/{job_id}")
def detalj_oglasa(job_id: str, request: Request):
    _limit(api_limiter, request.client.host if request.client else "x", "Previše zahtjeva.")
    o = store.detalji(job_id)
    if not o:
        raise HTTPException(404, "Oglas nije pronađen.")
    return o


@app.post("/api/search", response_model=SearchResponse)
def pretraga(body: SearchIn, request: Request):
    ip = request.client.host if request.client else "x"
    _limit(ai_limiter, f"ai:{ip}", "AI budžet iscrpljen za ovu minutu, pokušajte kasnije.")
    try:
        ai = tumaci_upit(body.upit)
    except AiNedostupan as e:
        # Iskrena degradacija: AI nedostupan -> lokalni parser ključnih riječi.
        # Rezultati su označeni u ai_napomena, nikad se ne predstavljaju kao AI.
        ai = RezultatAI(
            parsiraj_kriterije(body.upit),
            f"AI jezgro nedostupno ({e}). Prikazani rezultati su po ključnim riječima.",
            "lokalni-parser",
        )
    k: Kriteriji = ai.kriteriji
    if body.geo_prioritet:
        doz = {"bih", "balkan", "europa", "svijet"}
        k.geo_prioritet = [g for g in body.geo_prioritet if g in doz] or k.geo_prioritet  # type: ignore[assignment]
    # Rangira se cijeli aktivni skup; ranije je rez bio 500 (prvih 500 po redoslijedu
    # skena), zbog čega izvori skenirani kasnije nikad nisu ulazili u pretragu.
    rows = store.svi()
    rangirani: list[RangiraniOglas] = []
    for o in rows:
        ocjena, za, protiv = rangiraj(o, k)
        rangirani.append(RangiraniOglas(oglas=o, ocjena=ocjena, zasto_odgovara=za, zasto_ne_odgovara=protiv))  # type: ignore[arg-type]
    rangirani.sort(key=lambda r: r.ocjena, reverse=True)
    start = (body.stranica - 1) * body.po_stranici
    return SearchResponse(kriteriji=k, ukupno=len(rangirani),
                          rezultati=rangirani[start:start + body.po_stranici], ai_napomena=ai.napomena)


@app.get("/api/sources")
def izvori():
    brojevi = store.broj_po_izvoru()
    return [{"id": cid, **connectors.META_IZVORA.get(cid, {"url": "", "pristup": "javan"}),
             "naziv": getattr(connectors.REGISTAR[cid], "naziv", cid),
             "obuhvat": getattr(connectors.REGISTAR[cid], "obuhvat", ""),
             "oglasa": brojevi.get(cid, 0)} for cid in connectors.REGISTAR]


@app.get("/api/sources/health")
def izvori_status():
    return {"izvori": list(connectors.REGISTAR.keys()), "napomena": "Detaljan status je u admin skeniranju."}


def _admin_ok(token: str | None) -> None:
    if not provjeri_admin(token or "", settings.ADMIN_TOKEN):
        raise HTTPException(401, "Neautorizirano.")


@app.post("/api/admin/scan")
def admin_sken(request: Request, x_admin_token: str | None = Header(default=None), izvor: str | None = None):
    _admin_ok(x_admin_token)
    _limit(ai_limiter, "admin", "Previše skeniranja.")
    return {"skeniranja": admin.pokreni_sken(izvor)}


@app.get("/api/admin/status")
def admin_status(x_admin_token: str | None = Header(default=None)):
    _admin_ok(x_admin_token)
    return {"izvori": list(connectors.REGISTAR.keys())}


@app.exception_handler(HTTPException)
def _http_greska(request: Request, exc: HTTPException):
    return JSONResponse({"greska": exc.detail}, status_code=exc.status_code)


@app.exception_handler(Exception)
def _greska(request: Request, exc: Exception):
    return JSONResponse({"greska": "Interna greška."}, status_code=500)  # bez stack tracea klijentu
