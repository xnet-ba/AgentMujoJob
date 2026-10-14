"""Testovi mapiranja konektora na sintetičkim payloadima — bez mreže."""
import app.connectors as c


def test_remotive_mapiranje(monkeypatch):
    monkeypatch.setattr(c, "_fetch_json", lambda *a, **k: {"jobs": [
        {"id": 1, "title": "Dev", "company_name": "ACME", "candidate_required_location": "EU",
         "description": "<p>Python</p>", "url": "https://remotive.com/x", "publication_date": "2026-10-01T00:00:00"}]})
    o, nap = c.RemotiveKonektor().skeniraj()
    assert nap is None and len(o) == 1 and o[0]["vrsta_rada"] == "remote" and "Python" in o[0]["opis"]


def test_remoteok_preskace_pravnu_napomenu(monkeypatch):
    monkeypatch.setattr(c, "_fetch_json", lambda *a, **k: [
        {"legal": "notice"}, {"id": "5", "position": "Dev", "company": "ACME",
                              "salary_min": "0", "salary_max": "100000", "url": "https://remoteok.com/x"}])
    o, nap = c.RemoteokKonektor().skeniraj()
    assert len(o) == 1 and o[0]["plata_min"] is None and o[0]["plata_max"] == 100000.0
    assert o[0]["plata_valuta"] == "USD"


def test_rss_mapiranje(monkeypatch):
    xml = ('<rss><channel><item><title>Kuhar</title><link>https://www.posao.hr/o/1</link>'
           '<description>Posao</description><pubDate>Mon, 01 Jan 2026</pubDate></item>'
           '<item><title>Bez linka</title></item></channel></rss>').encode()
    monkeypatch.setattr(c, "_fetch", lambda *a, **k: xml)
    kon = c.RssKonektor("t", "T", "https://www.posao.hr/rss/", "Hrvatska", "Hrvatska")
    o, nap = kon.skeniraj()
    assert len(o) == 1 and o[0]["drzava"] == "Hrvatska"  # oglas bez URL-a se odbacuje


def test_registar_sadrzi_sve_verificirane_izvore():
    assert set(c.REGISTAR) >= {"greenhouse-eu", "remotive", "remoteok", "arbeitnow",
                               "jobtech-se", "eures", "posao-hr-rss", "wwr-rss"}
    assert set(c.META_IZVORA) >= set(c.REGISTAR)
