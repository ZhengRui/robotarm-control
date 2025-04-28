import atexit
import logging
import logging.handlers
import queue
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Determine the backend directory (2 levels up from the utils directory)
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent

# Create a queue for thread-safe logging
log_queue: queue.Queue = queue.Queue(-1)  # -1 means unlimited size
queue_handler = logging.handlers.QueueHandler(log_queue)

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "%(asctime)s, %(levelname)-8s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
)
console_handler.setFormatter(formatter)

# Start the listener thread
listener = logging.handlers.QueueListener(log_queue, console_handler)
listener.start()


def get_logger(
    name: str, log_level: int = logging.INFO, log_to_file: bool = False, log_dir: str = "logs"
) -> logging.Logger:
    """
    Create and return a logger with the given name and configuration.

    Args:
        name (str): The name of the logger
        log_level (int): The logging level (default: logging.INFO)
        log_to_file (bool): Whether to log to a file (default: False)
        log_dir (str): Directory to store log files if log_to_file is True.
                       If relative path, it will be relative to the backend directory.
                       If absolute path, it will be used as is.

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Disable propagation to parent loggers to prevent duplicate logs
    logger.propagate = False

    # Add queue handler for thread-safe logging
    logger.addHandler(queue_handler)

    # Add file handler if requested
    if log_to_file:
        # Handle relative vs absolute paths
        log_path = Path(log_dir)
        if not log_path.is_absolute():
            # If it's a relative path, make it relative to the project root
            log_path = BACKEND_ROOT / log_path

        # Create directory if it doesn't exist
        if not log_path.exists():
            log_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_path / f"{name}_{timestamp}.log"

        file_handler = logging.FileHandler(str(log_file))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Create a default logger for direct import
default_logger = get_logger("default")


# Convenience methods to avoid having to import both logging and this module
def debug(msg: Any, *args: Any, **kwargs: Any) -> None:
    default_logger.debug(msg, *args, **kwargs)


def info(msg: Any, *args: Any, **kwargs: Any) -> None:
    default_logger.info(msg, *args, **kwargs)


def warning(msg: Any, *args: Any, **kwargs: Any) -> None:
    default_logger.warning(msg, *args, **kwargs)


def error(msg: Any, *args: Any, **kwargs: Any) -> None:
    default_logger.error(msg, *args, **kwargs)


def critical(msg: Any, *args: Any, **kwargs: Any) -> None:
    default_logger.critical(msg, *args, **kwargs)


# Stop the listener when the program exits
atexit.register(listener.stop)


# Usage examples:
#
# 1. Simple usage with default logger:
#    from logger import info, error
#    info("Application started")
#    error("Something went wrong")
#
# 2. Create a custom logger:
#    from logger import get_logger
#    logger = get_logger("robot_arm", log_to_file=True)
#    logger.info("Robot arm initialized")
#    logger.error("Motor failure detected")
