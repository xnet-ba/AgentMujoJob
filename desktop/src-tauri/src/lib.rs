use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::{Manager, RunEvent};

/// Drži ručku ka backend sidecar procesu da ga možemo ugasiti pri izlasku.
struct BackendProces(Mutex<Option<Child>>);

/// Pokreće `agentmujojob-backend` iz bundlanih resursa (ako postoji).
/// OpenCode CLI se bundla uz njega i predaje backendu kroz OPENCODE_BIN.
fn pokreni_backend(app: &tauri::AppHandle) -> Option<Child> {
    let dir = app
        .path()
        .resolve("binaries", tauri::path::BaseDirectory::Resource)
        .ok()?;
    let exe = dir.join("agentmujojob-backend.exe");
    if !exe.exists() {
        return None;
    }

    let mut cmd = Command::new(exe);
    cmd.env("APP_ENV", "prod")
        .env("BACKEND_HOST", "127.0.0.1")
        .env("BACKEND_PORT", "8010")
        .env(
            "CORS_ORIGINS",
            "http://tauri.localhost,https://tauri.localhost,http://localhost:3000",
        );

    let opencode = dir.join("opencode.exe");
    if opencode.exists() {
        cmd.env("OPENCODE_BIN", opencode);
    }

    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        // Bez konzolnog prozora za backend proces.
        cmd.creation_flags(0x0800_0000);
    }

    cmd.spawn().ok()
}

/// Otvara URL u podrazumijevanom sistemskom pregledaču (Tauri WebView2 blokira `target="_blank"`).
/// Samo http/https, bez navodnika/bijelih znakova; `explorer.exe` prima URL kao zaseban argument
/// (bez shell parsiranja, pa `&` u upitu ne može razbiti komandu).
#[tauri::command]
fn otvori_url(url: String) -> Result<(), String> {
    let dozvoljeno = (url.starts_with("http://") || url.starts_with("https://"))
        && url.len() <= 2048
        && !url.chars().any(|c| c == '"' || c == '\'' || c.is_whitespace() || c.is_control());
    if !dozvoljeno {
        return Err("nedozvoljen link".to_string());
    }
    #[cfg(windows)]
    {
        Command::new("explorer.exe")
            .arg(&url)
            .spawn()
            .map_err(|e| e.to_string())?;
        Ok(())
    }
    #[cfg(not(windows))]
    {
        let _ = url;
        Err("otvaranje linkova je podrzano samo na Windowsu".to_string())
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            if let Some(w) = app.get_webview_window("main") {
                let _ = w.set_title("AgentMujoJob");
            }
            let child = pokreni_backend(app.handle());
            app.manage(BackendProces(Mutex::new(child)));
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![otvori_url])
        .build(tauri::generate_context!())
        .expect("AgentMujoJob se nije pokrenuo")
        .run(|app, event| {
            if let RunEvent::Exit = event {
                if let Some(mut child) = app.state::<BackendProces>().0.lock().unwrap().take() {
                    let _ = child.kill();
                }
            }
        });
}
