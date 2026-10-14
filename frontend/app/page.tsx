"use client";
import { useState } from "react";
import { pretrazi, plata, type Rangirani } from "../lib/api";

export default function Pocetna() {
  const [upit, setUpit] = useState("");
  const [stanje, setStanje] = useState<"idle" | "ucitava" | "gotovo" | "greska" | "offline">("idle");
  const [rez, setRez] = useState<Rangirani[]>([]);
  const [ukupno, setUkupno] = useState(0);
  const [poruka, setPoruka] = useState("");

  async function trazi(e: React.FormEvent) {
    e.preventDefault();
    if (upit.trim().length < 2) return;
    setStanje("ucitava"); setPoruka("");
    try {
      const r = await pretrazi(upit);
      setRez(r.rezultati); setUkupno(r.ukupno); setStanje("gotovo");
    } catch (err) {
      setStanje(navigator.onLine === false ? "offline" : "greska");
      setPoruka("Server nije dostupan. Provjerite vezu pa pokušajte ponovo.");
    }
  }

  return (
    <div className="wrap">
      <h1>Pronađi posao koji ti odgovara.</h1>
      <p className="pod">Pretraži oglase u BiH, regionu i svijetu uz pomoć AI asistenta.</p>
      <form onSubmit={trazi}>
        <input type="text" value={upit} onChange={(e) => setUpit(e.target.value)}
          placeholder="npr. Terenski komercijalist u Tešnju, plata najmanje 1800 KM" aria-label="Pretraga prirodnim jezikom" />
        <button type="submit" disabled={stanje === "ucitava"}>Pretraži poslove</button>
      </form>
      {stanje === "ucitava" && <p>Učitavam…</p>}
      {(stanje === "greska" || stanje === "offline") && (
        <div className="greska"><p>{poruka}</p><button onClick={trazi}>Pokušaj ponovo</button></div>)}
      {stanje === "gotovo" && (
        <>
          <p role="status">Pronađeno rezultata: {ukupno}</p>
          {rez.length === 0 && (<div className="prazno"><p>Nema rezultata. Pokušajte izmijeniti kriterije (grad, zanimanje, remote).</p></div>)}
          {rez.map((r) => (
            <article className="kartica" key={r.oglas.id}>
              <h2>{r.oglas.naslov}</h2>
              <p className="meta">{r.oglas.poslodavac ?? "Nije navedeno"} · {r.oglas.lokacija ?? "Nije navedeno"} · {r.oglas.drzava ?? "Nije navedeno"} · {r.oglas.datum_objave ?? "Datum nepoznat"} · Izvor: {r.oglas.izvor}</p>
              <p>Plata: {plata(r.oglas)}</p>
              <p className="ocjena">Relevantnost: {r.ocjena}% (procjena, ne garancija)</p>
              <ul>{r.zasto_odgovara.map((z, i) => <li key={i}>{z}</li>)}</ul>
              <a href={r.oglas.original_url} target="_blank" rel="noopener noreferrer">Otvori originalni oglas</a>
            </article>))}
        </>)}
    </div>
  );
}
