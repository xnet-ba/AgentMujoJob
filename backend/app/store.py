"""Skladištenje: Appwrite REST kada je konfiguriran, inače lokalni JSON (idempotentno)."""
from __future__ import annotations

import json
import os
import uuid

import httpx

from .config import settings
from .dedup import dedup
from .models import sada_iso


class Store:
    def __init__(self, data_dir: str | None = None):
        self.data_dir = data_dir or settings.DATA_DIR
        os.makedirs(self.data_dir, exist_ok=True)
        self.jobs_path = os.path.join(self.data_dir, "jobs.json")
        self.runs_path = os.path.join(self.data_dir, "scan_runs.json")
        for p in (self.jobs_path, self.runs_path):
            if not os.path.exists(p):
                with open(p, "w") as f:
                    json.dump([], f)

    @property
    def appwrite(self) -> bool:
        return bool(settings.APPWRITE_PROJECT_ID and settings.APPWRITE_API_KEY and settings.APPWRITE_DB_ID)

    # -- lokalni JSON backend --
    def _read(self, p: str) -> list:
        try:
            with open(p) as f:
                return json.load(f)
        except Exception:
            return []

    def _write(self, p: str, rows: list) -> None:
        tmp = p + ".tmp"
        with open(tmp, "w") as f:
            json.dump(rows, f, ensure_ascii=False)
        os.replace(tmp, p)

    def upsert(self, oglasi: list[dict]) -> tuple[int, int]:
        postojeci = self._read(self.jobs_path)
        po_id = {o["id"]: o for o in postojeci}
        novi = 0
        for o in dedup(oglasi):
            if o["id"] in po_id:
                staro = po_id[o["id"]]
                o["prvi_put_vidjen"] = staro.get("prvi_put_vidjen", o["prvi_put_vidjen"])
                po_id[o["id"]] = o
            else:
                po_id[o["id"]] = o
                novi += 1
        self._write(self.jobs_path, list(po_id.values()))
        return len(oglasi), novi

    def listaj(self, filteri: dict | None = None, stranica: int = 1, po_stranici: int = 20) -> tuple[list[dict], int]:
        filteri = filteri or {}
        rows = [o for o in self._read(self.jobs_path) if o.get("status", "aktivan") == "aktivan"]
        for klj in ("drzava", "kategorija", "vrsta_rada", "vrsta_ugovora"):
            if filteri.get(klj):
                rows = [o for o in rows if (o.get(klj) or "").lower() == filteri[klj].lower()]
        if filteri.get("grad"):
            rows = [o for o in rows if filteri["grad"].lower() in (o.get("lokacija") or "").lower()]
        if filteri.get("q"):
            q = filteri["q"].lower()
            rows = [o for o in rows if q in f"{o.get('naslov','')} {o.get('opis','')} {o.get('poslodavac','')}".lower()]
        ukupno = len(rows)
        start = (max(1, stranica) - 1) * po_stranici
        return rows[start:start + po_stranici], ukupno

    def detalji(self, job_id: str) -> dict | None:
        for o in self._read(self.jobs_path):
            if o.get("id") == job_id:
                return o
        return None

    def zabiljezi_sken(self, izvor: str, pronadjeno: int, dodano: int, greska: str | None) -> dict:
        runs = self._read(self.runs_path)
        run = {"id": uuid.uuid4().hex[:12], "izvor": izvor, "pocetak": sada_iso(),
               "kraj": sada_iso(), "pronadjeno": pronadjeno, "dodano": dodano, "greska": greska}
        runs.append(run)
        self._write(self.runs_path, runs[-200:])
        return run


store = Store()
