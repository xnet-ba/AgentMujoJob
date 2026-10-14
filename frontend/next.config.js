/** @type {import('next').NextConfig} */
const nextConfig = { output: process.env.TAURI_BUILD ? "export" : undefined, images: { unoptimized: !!process.env.TAURI_BUILD } };
module.exports = nextConfig;
