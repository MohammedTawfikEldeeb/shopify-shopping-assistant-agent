from loguru import logger as loguru_logger
import os
import sys

def setup_logging(log_level: str | None = None):
    """Return a project-wide Loguru logger."""

    log_level = log_level or os.getenv("LOG_LEVEL", "DEBUG").upper()

    loguru_logger.remove()
    loguru_logger.add(
        sys.stdout,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level}</level> | <cyan>{module}</cyan>:<cyan>{function}</cyan> - "
        "<level>{message}</level>",
    )
    loguru_logger.debug(f"Logging initialized at {log_level} level (Loguru).")
    return loguru_logger