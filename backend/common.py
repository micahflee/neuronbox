import os
import appdirs

def get_config_dir():
    return appdirs.user_config_dir("neuronbox")

def get_models_dir():
    return os.path.join(get_config_dir(), "models")