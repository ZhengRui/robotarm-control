import logging
import os
import sys
from datetime import datetime


def get_logger(name, log_level=logging.INFO, log_to_file=False, log_dir="logs"):
    """
    Create and return a logger with the given name and configuration.

    Args:
        name (str): The name of the logger
        log_level (int): The logging level (default: logging.INFO)
        log_to_file (bool): Whether to log to a file (default: False)
        log_dir (str): Directory to store log files if log_to_file is True

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s, %(levelname)-8s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d:%H:%M:%S",
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Add file handler if requested
    if log_to_file:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Create a default logger for direct import
default_logger = get_logger("default")


# Convenience methods to avoid having to import both logging and this module
def debug(msg, *args, **kwargs):
    default_logger.debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    default_logger.info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    default_logger.warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    default_logger.error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    default_logger.critical(msg, *args, **kwargs)


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
