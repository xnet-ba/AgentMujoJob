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


def test_klix_mapiranje_jobposting(monkeypatch):
    import json
    xml = ('<?xml version="1.0"?><urlset><url><loc>https://posao.klix.ba/oglasi/kuhar/10887</loc>'
           '</url></urlset>').encode()
    jp = {"@context": "https://schema.org", "@type": "JobPosting", "title": "Kuhar (m/ž)",
          "description": "<p>Priprema jela</p>", "datePosted": "2026-10-20T08:00:00Z",
          "employmentType": "FULL_TIME", "hiringOrganization": {"name": "Hotel X"},
          "jobLocation": {"address": {"addressLocality": "Sarajevo", "addressCountry": "BA"}},
          "baseSalary": {"currency": "BAM", "value": {"minValue": 1500, "maxValue": 2000}},
          "url": "https://posao.klix.ba/oglasi/kuhar/10887"}
    stranica = ('<html><script type="application/ld+json">' + json.dumps(jp, ensure_ascii=False)
                + "</script></html>").encode()

    def lazni(url, *a, **k):
        return xml if "sitemap" in url else stranica
    monkeypatch.setattr(c, "_fetch", lazni)
    o, nap = c.KlixPosaoKonektor().skeniraj()
    assert nap is None and len(o) == 1
    assert o[0]["poslodavac"] == "Hotel X" and o[0]["drzava"] == "Bosna i Hercegovina"
    assert o[0]["plata_min"] == 1500.0 and o[0]["plata_max"] == 2000.0
    assert o[0]["datum_objave"] == "2026-10-20" and o[0]["vrsta_ugovora"] == "puno radno vrijeme"


def test_mojposao_kartice(monkeypatch):
    html = ('<div><img alt="Hotel X"><a href="/posao/abc/kuhar">'
            '<h3 data-test="job-card-content-title">Kuhar</h3></a>'
            '<span class="info__child"><!--[-->Sarajevo<!--]--></span></div>').encode()
    monkeypatch.setattr(c, "_fetch", lambda *a, **k: html)
    o, nap = c.MojposaoKonektor().skeniraj()
    assert nap is None and len(o) == 1
    assert o[0]["naslov"] == "Kuhar" and o[0]["poslodavac"] == "Hotel X"
    assert o[0]["lokacija"] == "Sarajevo" and o[0]["original_url"].endswith("/posao/abc/kuhar")


def test_registar_sadrzi_sve_verificirane_izvore():
    assert set(c.REGISTAR) >= {"klix-posao", "mojposao-ba", "greenhouse-eu", "remotive",
                               "remoteok", "arbeitnow", "jobtech-se", "eures",
                               "posao-hr-rss", "wwr-rss"}
    assert set(c.META_IZVORA) >= set(c.REGISTAR)
