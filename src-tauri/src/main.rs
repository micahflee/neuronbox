#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;
use std::sync::mpsc;
use tauri::api::dialog::FileDialogBuilder;
use tauri::api::dialog::{MessageDialogBuilder, MessageDialogKind, MessageDialogButtons};
use std::thread;
use std::time::Duration;
use reqwest;

#[derive(serde::Deserialize)]
struct Params;

#[derive(serde::Serialize)]
struct Response {
    file_path: Option<String>,
}

fn main() {
    // Start the backend process in the background
    Command::new("./resources/backend")
        .spawn()
        .expect("Failed to start the backend process");

    // TODO: move this block_until_backend_ready() to the frontend UI, so that a window will launch immediately and it can show a loading graphic

    // Block until the backend is ready
    block_until_backend_ready();

    // TODO: when the window closes, kill the backend process

    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![select_file, message_dialog])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn block_until_backend_ready() {
    let client = reqwest::blocking::Client::new();
    let health_url = "http://127.0.0.1:52014/health";

    loop {
        match client.get(health_url).send() {
            Ok(response) if response.status().is_success() => {
                println!("Backend is ready!");
                break;
            }
            _ => {
                println!("Backend is not ready yet, waiting for 1 second...");
                thread::sleep(Duration::from_secs(1));
            }
        }
    }
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