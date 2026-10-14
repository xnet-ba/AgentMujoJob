"""Administrativno skeniranje: konektori -> normalizacija -> dedup -> store."""
from __future__ import annotations

from . import connectors
from .models import sada_iso
from .normalize import normaliziraj
from .store import store


def pokreni_sken(izvor_id: str | None = None) -> list[dict]:
    rez: list[dict] = []
    ciljevi = [izvor_id] if izvor_id else list(connectors.REGISTAR.keys())
    for cid in ciljevi:
        kon = connectors.REGISTAR.get(cid)
        if kon is None:
            rez.append(store.zabiljezi_sken(cid, 0, 0, "nepoznat izvor"))
            continue
        try:
            sirovi, napomena = kon.skeniraj()  # type: ignore[attr-defined]
            norm = []
            for s in sirovi:
                try:
                    norm.append(normaliziraj(s, cid).model_dump())
                except ValueError:
                    continue
            pron, dod = store.upsert(norm)
            rez.append(store.zabiljezi_sken(cid, pron, dod, napomena))
        except Exception as e:
            rez.append(store.zabiljezi_sken(cid, 0, 0, f"greška: {e}"[:300]))
    return rez
