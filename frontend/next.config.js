// Export (statički out/) za Tauri kad postoji frontend/.tauri-export flag
// (pravi ga CI prije builda) ili TAURI_BUILD=1. Obični `npm run build`
// ostaje serverski (za `next start` iza reverse proxyja).
// Flag se čita iz frontend direktorija gdje i nalazi se next.config.js.
const fs = require("fs");
const path = require("path");
const flag = path.join(__dirname, ".tauri-export");
const jeExport = fs.existsSync(flag) || !!process.env.TAURI_BUILD;
const nextConfig = { output: jeExport ? "export" : undefined, images: { unoptimized: jeExport } };
module.exports = nextConfig;