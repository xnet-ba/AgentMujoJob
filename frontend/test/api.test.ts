import test from "node:test";
import assert from "node:assert/strict";
import { plata } from "../lib/api.js";

test("plata prikazuje Nije navedeno kad nema podataka", () => {
  assert.equal(plata({ id: "1", naslov: "x", izvor: "t", original_url: "https://x", vrsta_rada: "nepoznato" }), "Nije navedeno");
});
test("plata prikazuje raspon", () => {
  assert.ok(plata({ id: "1", naslov: "x", izvor: "t", original_url: "https://x", vrsta_rada: "lokacija", plata_min: 1800, plata_max: 2200, plata_valuta: "BAM" }).includes("1800"));
});
