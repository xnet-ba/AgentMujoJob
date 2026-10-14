use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            if let Some(w) = app.get_webview_window("main") {
                let _ = w.set_title("AgentMujoJob");
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("AgentMujoJob se nije pokrenuo");
}
