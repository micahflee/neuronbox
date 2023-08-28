#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use nix::sys::signal::{kill, SIGTERM};
use nix::unistd::Pid;
use std::process::Command;
use std::sync::mpsc;
use std::sync::{Arc, Mutex};
use sysinfo::{PidExt, ProcessExt, System, SystemExt};
use tauri::api::dialog::FileDialogBuilder;
use tauri::api::dialog::{MessageDialogBuilder, MessageDialogButtons, MessageDialogKind};

#[derive(serde::Deserialize)]
struct Params;

#[derive(serde::Serialize)]
struct Response {
    file_path: Option<String>,
}

fn main() {
    // If backend processes are already running in the background, kill them
    kill_backend_processes();

    // Run `python backend.py` in debug mode, or `./resources/backend` in release mode
    let backend_cmd = if cfg!(debug_assertions) {
        "python"
    } else {
        "./resources/neuronbox-backend"
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
            .expect("Failed to start the backend process"),
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
                                    }
                                    Ok(None) => {
                                        // The process is still alive, kill it forcefully
                                        process.kill().expect("Failed to kill the backend process");
                                    }
                                    Err(e) => {
                                        println!("Error waiting for process: {:?}", e);
                                    }
                                }
                            }
                            Err(e) => {
                                println!("Failed to send SIGTERM: {:?}", e);
                            }
                        }
                    }

                    #[cfg(windows)]
                    {
                        // TODO: kill processes in Windows
                    }
                }
                _ => {}
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn kill_backend_processes() {
    let sys = System::new_all();
    let backend_name = if cfg!(debug_assertions) {
        "python"
    } else {
        "neuronbox-backend"
    };
    let backend_cmd_line = if cfg!(debug_assertions) {
        vec!["../backend.py"]
    } else {
        vec!["neuronbox-backend"]
    };
    for (pid, proc) in sys.processes() {
        let cmd = proc.cmd();

        // Extract the filename from the full path
        let binary_name = cmd
            .get(0)
            .and_then(|path| path.split('/').last())
            .unwrap_or("");

        // Check if the extracted binary name matches "python" or "Python"
        if binary_name.to_lowercase() == backend_name
            && cmd.len() >= backend_cmd_line.len()
            && &cmd[(cmd.len() - backend_cmd_line.len())..] == &backend_cmd_line[..]
        {
            println!("Found backend process with PID {}", pid);
            #[cfg(unix)]
            {
                let pid = Pid::from_raw(pid.as_u32().try_into().unwrap());
                println!("Killing process {}...", pid);
                if let Err(e) = kill(pid, SIGTERM) {
                    println!("Failed to send SIGTERM to process {}: {:?}", pid, e);
                } else {
                    std::thread::sleep(std::time::Duration::from_millis(100));
                }
            }
            #[cfg(windows)]
            {
                // TODO: kill processes in Windows
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
    })
    .await
    .unwrap();

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
