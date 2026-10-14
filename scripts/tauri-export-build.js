const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const root = path.join(__dirname, "..");
const frontend = path.join(root, "frontend");
const flag = path.join(frontend, ".tauri-export");
const outIndex = path.join(frontend, "out", "index.html");

try {
  fs.writeFileSync(flag, "x");
  console.log("flag created:", flag, "exists:", fs.existsSync(flag));
  
  const win = process.platform === "win32";
  const progFiles = win ? (process.envProgramFiles || "C:\\\\Program Files") : undefined;
  const npmBin = win ? path.join(progFiles, "npm", "npm.cmd") : "npm";
  
  const buildEnv = { ...process.env, TAURI_BUILD: "1", NEXT_PUBLIC_API_URL: "https://posao.kolektiv.pro" };
  console.log("build env TAURI_BUILD:", buildEnv.TAURI_BUILD);
  console.log("flag exists in cwd:", fs.existsSync(path.join(process.cwd(), ".tauri-export")));
  
  const r = spawnSync(npmBin, ["run", "build"], {
    cwd: frontend,
    stdio: "inherit",
    shell: win,
    env: buildEnv,
  });
  
  console.log("build exit code:", r.status);
  if (r.status !== 0) {
    // Try to capture output by re-running with piped stdio
    const r2 = spawnSync(npmBin, ["run", "build"], {
      cwd: frontend,
      stdio: ["pipe", "pipe", "pipe"],
      shell: win,
      env: buildEnv,
    });
    console.log("stdout:", r2.stdout.toString().slice(0, 500));
    console.log("stderr:", r2.stderr.toString().slice(0, 500));
    if (r2.status !== 0) throw new Error("next build failed with code " + r2.status);
  }
  
  if (!fs.existsSync(outIndex)) throw new Error("nema frontend/out/index.html");
  console.log("tauri-export-build: OK");
} finally {
  try { fs.unlinkSync(flag); } catch (_) {}
}