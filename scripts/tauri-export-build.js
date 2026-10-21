const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const root = path.join(__dirname, "..");
const frontend = path.join(root, "frontend");
const flag = path.join(frontend, ".tauri-export");
const outIndex = path.join(frontend, "out", "index.html");

try {
  fs.writeFileSync(flag, "x");
  const win = process.platform === "win32";
  const npmBin = win ? "npm.cmd" : "npm";
  const r = spawnSync(npmBin, ["run", "build"], {
    cwd: frontend,
    stdio: "inherit",
    shell: win,
    env: { ...process.env, TAURI_BUILD: "1", NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8010" },
  });
  if (r.status !== 0) throw new Error("next build failed with code " + r.status);
  if (!fs.existsSync(outIndex)) throw new Error("nema frontend/out/index.html");
  console.log("tauri-export-build: OK");
} finally {
  try { fs.unlinkSync(flag); } catch (_) {}
}