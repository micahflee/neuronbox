#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;
use std::sync::mpsc;
use std::sync::{Arc, Mutex};
use tauri::api::dialog::FileDialogBuilder;
use tauri::api::dialog::{MessageDialogBuilder, MessageDialogKind, MessageDialogButtons};
use nix::sys::signal::{kill, SIGTERM};
use nix::unistd::Pid;

#[derive(serde::Deserialize)]
struct Params;

#[derive(serde::Serialize)]
struct Response {
    file_path: Option<String>,
}

fn main() {
    // Run `python backend.py` in debug mode, or `./resources/backend` in release mode
    let backend_cmd = if cfg!(debug_assertions) {
        "python"
    } else {
        "./resources/backend"
    };

    let backend_args = if cfg!(debug_assertions) {
        vec!["../backend.py"]
    } else {
        vec![]
    };

    // Start the backend process in the background
    let backend_process = Arc::new(Mutex::new(
        Command::new(backend_cmd)
            .args(&backend_args)
            .spawn()
            .expect("Failed to start the backend process")
    ));    

    // Start the app
    let process_clone = backend_process.clone();
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![select_file, message_dialog])
        .on_window_event(move |event| {
            match event.event() {
                tauri::WindowEvent::CloseRequested { .. } => {
                    let mut process = process_clone.lock().unwrap();

                    #[cfg(unix)]
                    {
                        let pid = Pid::from_raw(process.id() as i32);
                        // Send SIGTERM
                        match kill(pid, SIGTERM) {
                            Ok(_) => {
                                // Sleep for a bit to see if the process exits gracefully
                                std::thread::sleep(std::time::Duration::from_secs(1));

                                // Check if the process is still alive
                                match process.try_wait() {
                                    Ok(Some(_status)) => {
                                        // The process has terminated
                                    },
                                    Ok(None) => {
                                        // The process is still alive, kill it forcefully
                                        process.kill().expect("Failed to kill the backend process");
                                    },
                                    Err(e) => {
                                        println!("Error waiting for process: {:?}", e);
                                    }
                                }
                            },
                            Err(e) => {
                                println!("Failed to send SIGTERM: {:?}", e);
                            }
                        }
                    }

                    // ... other potential logic for non-unix systems ...
                }
                _ => {}
            }
        })
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