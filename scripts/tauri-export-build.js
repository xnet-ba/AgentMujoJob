// Windows-proof Tauri export build: bez shell varijabli, redirekcija i && lanaca.
// 1. upiše frontend/.tauri-export flag (next.config.js tada radi output:"export"),
// 2. pokrene `npm run build` s cwd=frontend i eksplicitnim envom (child_process,
//    varijable sigurno stižu do childa na svim platformama),
// 3. provjeri frontend/out/index.html, 4. obriše flag.
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const root = path.join(__dirname, "..");
const frontend = path.join(root, "frontend");
const flag = path.join(frontend, ".tauri-export");
const outIndex = path.join(frontend, "out", "index.html");

try {
  fs.writeFileSync(flag, "x");
  const r = spawnSync("npm", ["run", "build"], {
    cwd: frontend,
    stdio: "inherit",
    shell: false,
    env: { ...process.env, TAURI_BUILD: "1", NEXT_PUBLIC_API_URL: "https://posao.kolektiv.pro" },
  });
  if (r.status !== 0) throw new Error("next build pao s kodom " + r.status);
  if (!fs.existsSync(outIndex)) throw new Error("nema frontend/out/index.html — export nije uspio");
  console.log("tauri-export-build: OK", outIndex);
} finally {
  try { fs.unlinkSync(flag); } catch (_) { /* već obrisan */ }
}
