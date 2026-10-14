# Windows 11 build

Desktop = Tauri 2 omotač oko istog frontenda. Lokalna izgradnja treba Rust (nije dostupan na serveru) pa je primarni put **GitHub Actions `windows-build.yml`** (windows-latest): `TAURI_BUILD=1 npm run build` → `tauri-action` → `.msi` artefakt. Bez ugrađenih tajni; backend URL se podešava u aplikaciji (`NEXT_PUBLIC_API_URL`). Potpisivanje: nema certifikata — dokumentirano, SmartScreen može upozoriti. Instalacija: Start meni + deinstalacija standardno kroz .msi.
