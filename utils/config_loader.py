from omegaconf import OmegaConf, DictConfig
from pathlib import Path


def load_config() -> DictConfig:
    current_file = Path(__file__)
    project_root = current_file.parent.parent
    config_path = project_root / "config.yaml"
    
    if not config_path.exists():
        config_path = Path("config.yaml")
        if not config_path.exists():
            raise FileNotFoundError(
                f"config.yaml не найден. Искали в: {project_root / 'config.yaml'} и {Path('config.yaml').absolute()}"
            )
    
    config = OmegaConf.load(config_path)

    if not isinstance(config, DictConfig):
        raise TypeError("Loaded config is not a DictConfig")

    return config


config = load_config()
