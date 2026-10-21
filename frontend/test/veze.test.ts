import test from "node:test";
import assert from "node:assert/strict";
import { otvoriSpolja, type Prozor } from "../lib/veze.js";

test("u Tauri otvara link preko Rust komande", () => {
  const pozivi: Array<[string, Record<string, unknown> | undefined]> = [];
  const w: Prozor = { __TAURI__: { core: { invoke: async (k, a) => { pozivi.push([k, a]); } } } };
  otvoriSpolja("https://posao.klix.ba/oglas/1", w);
  assert.deepEqual(pozivi, [["otvori_url", { url: "https://posao.klix.ba/oglas/1" }]]);
});

test("izvan Tauri koristi window.open", () => {
  const otvoreni: string[] = [];
  const w: Prozor = { open: (u) => { otvoreni.push(u); } };
  otvoriSpolja("https://example.com/posao", w);
  assert.deepEqual(otvoreni, ["https://example.com/posao"]);
});

test("ako Tauri komanda padne, link se otvara preko window.open", async () => {
  const otvoreni: string[] = [];
  const w: Prozor = {
    __TAURI__: { core: { invoke: async () => { throw new Error("nema dozvole"); } } },
    open: (u) => { otvoreni.push(u); },
  };
  otvoriSpolja("https://example.com/posao", w);
  await new Promise((r) => setTimeout(r, 0));
  assert.deepEqual(otvoreni, ["https://example.com/posao"]);
});
