import subprocess
import signal


def build_frontend():
    try:
        subprocess.run(["npm", "install"], cwd="neuronbox/frontend", check=True)
        subprocess.run(
            ["npm", "run", "build", "-m", "development"],
            cwd="neuronbox/frontend",
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def start_server():
    process = None
    try:
        process = subprocess.Popen(
            ["gunicorn", "neuronbox.app:app", "-w", "4", "-b", "127.0.0.1:5000"]
        )
        process.communicate()
    except KeyboardInterrupt:
        if process:
            process.send_signal(signal.SIGTERM)
