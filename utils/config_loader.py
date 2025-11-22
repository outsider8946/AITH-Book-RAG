from pathlib import Path
from omegaconf import OmegaConf, DictConfig

def load_config() -> DictConfig:
    config_path = 'config.yaml'
    config = OmegaConf.load(config_path)

    if not isinstance(config, DictConfig):
        raise TypeError("Loaded config is not a DictConfig")
    
    return config

config = load_config()