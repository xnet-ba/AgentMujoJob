const fs = require("fs");
const path = require("path");
/** @type {import('next').NextConfig} */
// Export (statički out/) za Tauri kad postoji frontend/.tauri-export flag
// (pravi ga CI prije builda) ili TAURI_BUILD=1. Obični `npm run build`
// ostaje serverski (za `next start` iza reverse proxyja).
const flag = fs.existsSync(path.join(__dirname, ".tauri-export"));
const jeExport = flag || !!process.env.TAURI_BUILD;
const nextConfig = { output: jeExport ? "export" : undefined, images: { unoptimized: jeExport } };
module.exports = nextConfig;
