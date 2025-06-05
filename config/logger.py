import os
import sys

from loguru import logger


def setup_logger() -> None:
    if os.getenv("DISABLE_LOGGING", "false").lower() == "true":
        logger.remove()
        return

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{message}</cyan>"
    )

    logger.remove()
    logger.add(
        sys.stdout,
        level="DEBUG",
        format=log_format,
        colorize=True,
        enqueue=True,
        filter=None,
    )

    logger.level("DEBUG", color="<blue>")
    logger.level("INFO", color="<green>")
    logger.level("SUCCESS", color="<light-green>")
    logger.level("WARNING", color="<yellow>")
    logger.level("ERROR", color="<red>")
    logger.level("CRITICAL", color="<bold red>")
