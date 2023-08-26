import os
import appdirs

# Config dirs


def get_config_dir():
    return appdirs.user_config_dir("neuronbox")


def get_models_dir():
    return os.path.join(get_config_dir(), "models")


# Download status helpers


def get_download_status_dir():
    return os.path.join(get_config_dir(), "download_status")


def create_status_file(key):
    with open(os.path.join(get_download_status_dir(), f"{key}.status"), "w") as f:
        f.write("0")  # Initially, progress is 0%


def update_status_file(key, progress):
    with open(os.path.join(get_download_status_dir(), f"{key}.status"), "w") as f:
        f.write(str(progress))


def read_status_file(key):
    try:
        with open(os.path.join(get_download_status_dir(), f"{key}.status"), "r") as f:
            return float(f.read().strip())
    except FileNotFoundError:
        return None
    except ValueError:
        return 0


def delete_status_file(key):
    try:
        os.remove(os.path.join(get_download_status_dir(), f"{key}.status"))
    except FileNotFoundError:
        pass


# Create folders if they don't exist

if not os.path.exists(get_models_dir()):
    os.makedirs(get_models_dir())

if not os.path.exists(get_download_status_dir()):
    os.makedirs(get_download_status_dir())
    # Delete any files left over from last time
    for filename in os.listdir(get_download_status_dir()):
        os.remove(os.path.join(get_download_status_dir(), filename))
