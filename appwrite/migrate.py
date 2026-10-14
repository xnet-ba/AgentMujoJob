"""Idempotentni provisioning Appwrite kolekcija (REST, stdlib-only). Bez ključa samo ispiše upute.

Environment: APPWRITE_ENDPOINT, APPWRITE_PROJECT_ID, APPWRITE_API_KEY, APPWRITE_DB_ID.
"""
import json
import os
import sys
import urllib.request

E = os.environ.get
ENDPOINT = E("APPWRITE_ENDPOINT", "https://baza.kolektiv.pro/v1").rstrip("/")
PROJECT = E("APPWRITE_PROJECT_ID", "")
KEY = E("APPWRITE_API_KEY", "")
DB = E("APPWRITE_DB_ID", "")

KOLEKCIJE = ["jobs", "job_sources", "scan_runs"]


def _req(method, path, body=None):
    r = urllib.request.Request(ENDPOINT + path, method=method,
                               data=json.dumps(body).encode() if body is not None else None,
                               headers={"X-Appwrite-Project": PROJECT, "X-Appwrite-Key": KEY,
                                        "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=20) as resp:
        return resp.status, resp.read().decode()[:2000]


def main():
    if not (PROJECT and KEY and DB):
        print("Nema Appwrite kredencijala — kolekcije NISU kreirane.")
        print("Upute: docs/APPWRITE-SETUP.md; logičke kolekcije:", ", ".join(KOLEKCIJE))
        return 0
    for c in KOLEKCIJE:
        try:
            st, _ = _req("GET", f"/databases/{DB}/collections/{c}")
            print(f"{c}: postoji (GET {st}) — preskačem kreiranje.")
        except Exception as e:
            print(f"{c}: provjera nije uspjela ({e}) — kreirajte ručno po docs/APPWRITE-SETUP.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
