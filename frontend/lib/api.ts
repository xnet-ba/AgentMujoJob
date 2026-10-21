export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8010";

export type Oglas = { id: string; naslov: string; poslodavac?: string | null; lokacija?: string | null; drzava?: string | null; plata_min?: number | null; plata_max?: number | null; plata_valuta?: string | null; datum_objave?: string | null; izvor: string; original_url: string; vrsta_rada: string; };
export type Rangirani = { oglas: Oglas; ocjena: number; zasto_odgovara: string[]; zasto_ne_odgovara: string[]; };
export type Izvor = { id: string; naziv?: string; obuhvat?: string; url?: string; oglasa?: number };

export async function pretrazi(upit: string): Promise<{ ukupno: number; rezultati: Rangirani[]; ai_napomena?: string }> {
  const r = await fetch(`${API_URL}/api/search`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ upit, po_stranici: 50 }) });
  if (!r.ok) throw new Error(`Greška pretrage (${r.status})`);
  return r.json();
}
export async function izvori(): Promise<Izvor[]> { const r = await fetch(`${API_URL}/api/sources`); if (!r.ok) throw new Error("Izvori nedostupni"); return r.json(); }
export function nazivIzvora(lista: Izvor[], id: string): string {
  return lista.find((i) => i.id === id)?.naziv || id;
}
export function plata(o: Oglas): string {
  if (o.plata_min != null || o.plata_max != null) return `${o.plata_min ?? "?"}–${o.plata_max ?? "?"} ${o.plata_valuta ?? ""}`.trim();
  return "Nije navedeno";
}
