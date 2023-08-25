import subprocess
import signal


def start_server():
    process = None
    try:
        process = subprocess.Popen(
            ["gunicorn", "app:app", "-w", "4", "-b", "127.0.0.1:5000"]
        )
        process.communicate()
    except KeyboardInterrupt:
        if process:
            process.send_signal(signal.SIGTERM)
