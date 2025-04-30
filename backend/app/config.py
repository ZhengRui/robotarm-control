import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

from lib.utils.logger import get_logger

# Initialize logger
logger = get_logger("config")

# Load environment variables from .env file
load_dotenv()

# Get environment settings
ENV = os.environ.get("ENV", "dev")
CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_config(env: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from YAML file based on environment.

    Args:
        env: Environment name (defaults to ENV environment variable or 'dev')

    Returns:
        Dictionary with configuration

    Raises:
        FileNotFoundError: If configuration file doesn't exist
    """
    # Use provided env or fallback to environment variable
    config_env = env or ENV

    # Construct path to config file
    config_path = CONFIG_DIR / f"{config_env}.yaml"

    if not config_path.exists():
        error_msg = f"Configuration file not found: {config_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {config_path}")
            return config
    except (yaml.YAMLError, IOError) as e:
        error_msg = f"Failed to load configuration from {config_path}: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


# Export configuration as a module-level variable
config = load_config()
