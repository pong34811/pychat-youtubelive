# Logging configuration for pychat-youtubelive
import logging
import os
from pathlib import Path

def setup_logging(log_file: str = "pychat.log"):
    """Configure root logger with console and file handlers.
    The log file is placed in the project's root directory.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Console handler with simple format
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (rotate daily would be overkill for this simple app)
    log_path = Path(__file__).resolve().parents[1] / log_file
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logger.info(f"Logging initialized, output to {log_path}")
    return logger
