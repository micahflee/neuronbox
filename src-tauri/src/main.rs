#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::mpsc;
use tauri::api::dialog::FileDialogBuilder;
use tauri::api::dialog::{MessageDialogBuilder, MessageDialogKind, MessageDialogButtons};

#[derive(serde::Deserialize)]
struct Params;

#[derive(serde::Serialize)]
struct Response {
    file_path: Option<String>,
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![select_file, message_dialog])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[tauri::command]
async fn select_file() -> String {
    let (tx, rx) = mpsc::channel();

    tokio::task::spawn_blocking(|| {
        FileDialogBuilder::new().pick_file(move |file_path| {
            let path_str = file_path
                .map(|p| p.to_str().unwrap().to_string())
                .unwrap_or_else(|| "".to_string());
            tx.send(path_str).unwrap();
        });
    }).await.unwrap();

    let received_path = rx.recv().unwrap();
    if received_path.is_empty() {
        "".to_string()
    } else {
        received_path
    }
}

#[tauri::command]
fn message_dialog(title: String, message: String, kind: String) {
    let dialog_kind = match kind.as_str() {
        "info" => MessageDialogKind::Info,
        "warning" => MessageDialogKind::Warning,
        "error" => MessageDialogKind::Error,
        _ => {
            eprintln!("Unknown kind '{}', defaulting to 'Info'", kind);
            MessageDialogKind::Info
        }
    };
    
    MessageDialogBuilder::new(&title, &message)
        .kind(dialog_kind)
        .buttons(MessageDialogButtons::Ok)
        .show(|_| {});
}