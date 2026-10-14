/** @type {import('next').NextConfig} */
// Export (statički out/) za Tauri: `npm run build:export` ili TAURI_BUILD=1.
// Obični `npm run build` ostaje serverski (za `next start` iza reverse proxyja).
const jeExport = process.env.TAURI_BUILD || process.env.npm_lifecycle_event === "build:export";
const nextConfig = { output: jeExport ? "export" : undefined, images: { unoptimized: !!jeExport } };
module.exports = nextConfig;
