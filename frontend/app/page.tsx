"use client";
import { useEffect, useState } from "react";
import { API_URL, izvori, nazivIzvora, plata, pretrazi, type Izvor, type Rangirani } from "../lib/api";

const PRIMJERI = [
  "kuhar u Sarajevu",
  "administrativni radnik Banja Luka",
  "remote React developer",
  "konobar Mostar",
];

const VRSTA: Record<string, string> = {
  lokacija: "Na lokaciji",
  hibrid: "Hibrid",
  remote: "Remote",
};

function Logo() {
  return (
    <span className="logo" aria-hidden="true">
      <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor"
        strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="7" width="18" height="13" rx="2.5" />
        <path d="M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7" />
        <path d="M3 12h18M10.5 12v2.2h3V12" />
      </svg>
    </span>
  );
}

function Skeleton() {
  return (
    <div className="oglas skeleton" aria-hidden="true">
      <div className="skeleton-linija w60" />
      <div className="skeleton-linija w35" />
      <div className="skeleton-linija w80" />
      <div className="skeleton-linija w45" />
    </div>
  );
}

export default function Pocetna() {
  const [upit, setUpit] = useState("");
  const [stanje, setStanje] = useState<"idle" | "ucitava" | "gotovo" | "greska" | "offline">("idle");
  const [rez, setRez] = useState<Rangirani[]>([]);
  const [ukupno, setUkupno] = useState(0);
  const [poruka, setPoruka] = useState("");
  const [napomena, setNapomena] = useState("");
  const [spremno, setSpremno] = useState(false);
  const [lista, setLista] = useState<Izvor[]>([]);

  // Backend sidecar se podiže uz aplikaciju; sačekaj health prije prve pretrage.
  useEffect(() => {
    let otkazano = false;
    (async () => {
      for (let i = 0; i < 120 && !otkazano; i++) {
        try {
          const r = await fetch(`${API_URL}/api/health`);
          if (r.ok && (await r.json()).spremno) { if (!otkazano) setSpremno(true); return; }
        } catch { /* servis još ne sluša */ }
        await new Promise((res) => setTimeout(res, 1000));
      }
      if (!otkazano) setSpremno(true);
    })();
    izvori().then((x) => { if (!otkazano) setLista(x); }).catch(() => { /* bez liste izvora UI i dalje radi */ });
    return () => { otkazano = true; };
  }, []);

  function trazi(e: React.FormEvent) {
    e.preventDefault();
    void posalji();
  }

  async function posalji(tekst?: string) {
    const q = (tekst ?? upit).trim();
    if (q.length < 2) return;
    setUpit(q);
    setStanje("ucitava"); setPoruka(""); setNapomena("");
    try {
      const r = await pretrazi(q);
      setRez(r.rezultati); setUkupno(r.ukupno); setNapomena(r.ai_napomena ?? ""); setStanje("gotovo");
    } catch {
      setStanje(navigator.onLine === false ? "offline" : "greska");
      setPoruka("Lokalni servis nije dostupan. Sačekajte trenutak pa pokušajte ponovo.");
    }
  }

  const ucitava = stanje === "ucitava";

  return (
    <>
      <header className="appbar">
        <div className="appbar-inner">
          <div className="brend">
            <Logo />
            <div>
              <strong>AgentMujoJob</strong>
              <span>Pretraga poslova · BiH i svijet</span>
            </div>
          </div>
          <div className={`status ${spremno ? "ok" : "ceka"}`}>
            <span className="tacka" />{spremno ? "Servis spreman" : "Pokrećem servis…"}
          </div>
        </div>
      </header>

      <div className="app">
      <section className="hero">
        <p className="eyebrow">Windows 11 · Lokalno · Bez naloga</p>
        <h1>Pronađi posao koji ti odgovara.</h1>
        <p className="pod">
          Jedna rečenica — a AI pronađe oglase, objasni zašto odgovaraju i vodi te direktno na original.
        </p>

        <form className="pretraga" onSubmit={trazi} aria-busy={ucitava}>
          <div className="polje">
            <svg className="ikona" viewBox="0 0 24 24" width="18" height="18" fill="none"
              stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
              <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
            </svg>
            <input id="upit" type="text" value={upit} onChange={(e) => setUpit(e.target.value)}
              placeholder="npr. terenski komercijalist u Tešnju, plata najmanje 1800 KM"
              aria-label="Pretraga prirodnim jezikom" autoComplete="off" />
          </div>
          <button type="submit" className="dugme" disabled={!spremno || ucitava}>
            {ucitava ? <span className="spiner" aria-hidden="true" /> : null}
            {ucitava ? "Tražim…" : spremno ? "Pretraži" : "Pokrećem…"}
          </button>
        </form>

        <div className="primjeri">
          <span>Pokušaj:</span>
          {PRIMJERI.map((p) => (
            <button key={p} type="button" className="cip" onClick={() => void posalji(p)}
              disabled={!spremno || ucitava}>{p}</button>
          ))}
        </div>
      </section>

      <main className="sadrzaj">
        {ucitava && (
          <div className="lista" aria-label="Učitavanje rezultata">
            <Skeleton /><Skeleton /><Skeleton />
          </div>
        )}

        {(stanje === "greska" || stanje === "offline") && (
          <div className="infobar greska" role="alert">
            <div>
              <strong>Pretraga nije uspjela</strong>
              <p>{poruka}</p>
            </div>
            <button type="button" className="dugme sekundarno" onClick={() => void posalji()}>Pokušaj ponovo</button>
          </div>
        )}

        {stanje === "gotovo" && (
          <section aria-live="polite">
            <div className="rezime">
              <p><strong>{ukupno}</strong> {ukupno === 1 ? "oglas" : "oglasa"} pronađeno
                <span className="odvoji">·</span> prikazano {rez.length}</p>
              <span className="znacka">Sortirano po relevantnosti</span>
            </div>

            {napomena && <p className="info"><span className="info-ikona" aria-hidden="true">i</span>{napomena}</p>}

            {rez.length === 0 && (
              <div className="prazno">
                <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor"
                  strokeWidth="1.6" strokeLinecap="round" aria-hidden="true">
                  <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
                </svg>
                <h2>Nema rezultata</h2>
                <p>Pokušaj šire kriterije — drugi grad, bez plate ili uključi remote.</p>
              </div>
            )}

            <div className="lista">
              {rez.map((r, idx) => {
                const vrsta = r.oglas.vrsta_rada && r.oglas.vrsta_rada !== "nepoznato"
                  ? VRSTA[r.oglas.vrsta_rada] ?? r.oglas.vrsta_rada : null;
                return (
                  <article className="oglas" key={r.oglas.id}>
                    <div className="oglas-vrh">
                      <div>
                        <h2>{r.oglas.naslov}</h2>
                        <p className="firma">
                          {r.oglas.poslodavac ?? "Nije navedeno"}
                          <span className="odvoji">·</span>
                          {r.oglas.lokacija ?? "Nije navedeno"}
                          {r.oglas.drzava ? <><span className="odvoji">·</span>{r.oglas.drzava}</> : null}
                        </p>
                      </div>
                      <div className="skor" title="Relevantnost (procjena, ne garancija)">
                        <span>{r.ocjena}<small>%</small></span>
                        <div className="traka"><i style={{ width: `${Math.max(0, Math.min(100, r.ocjena))}%` }} /></div>
                      </div>
                    </div>

                    <ul className="meta-red">
                      <li>{r.oglas.datum_objave ?? "Datum nepoznat"}</li>
                      <li>Plata: {plata(r.oglas)}</li>
                      <li className="cip-izvor">{nazivIzvora(lista, r.oglas.izvor)}</li>
                      {vrsta && <li>{vrsta}</li>}
                    </ul>

                    <div className="razlozi">
                      <ul className="za">
                        {r.zasto_odgovara.map((z, i) => <li key={i}>{z}</li>)}
                      </ul>
                      {r.zasto_ne_odgovara.length > 0 && (
                        <ul className="protiv">
                          {r.zasto_ne_odgovara.map((z, i) => <li key={i}>{z}</li>)}
                        </ul>
                      )}
                    </div>

                    <div className="oglas-dno">
                      <a className="veza" href={r.oglas.original_url} target="_blank" rel="noopener noreferrer">
                        Otvori originalni oglas
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor"
                          strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                          <path d="M7 17 17 7M9 7h8v8" />
                        </svg>
                      </a>
                      <span className="redni">#{idx + 1}</span>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
        )}
      </main>

      <footer className="panel izvori">
        <div className="panel-vrh">
          <h2>Izvori oglasa</h2>
          <span className="znacka">{lista.length} izvora</span>
        </div>
        <ul className="izvor-lista">
          {lista.map((i) => (
            <li key={i.id}>
              <span className="izvor-ime">
                {i.url
                  ? <a href={i.url} target="_blank" rel="noopener noreferrer">{i.naziv || i.id}</a>
                  : (i.naziv || i.id)}
              </span>
              {i.obuhvat && <span className="izvor-opis">{i.obuhvat}</span>}
              {typeof i.oglasa === "number" && <span className="izvor-broj">{i.oglasa}</span>}
            </li>
          ))}
        </ul>
        <p className="fino">Podaci ostaju na ovom računaru — bez naloga, historije i API ključeva.</p>
      </footer>
      </div>
    </>
  );
}
