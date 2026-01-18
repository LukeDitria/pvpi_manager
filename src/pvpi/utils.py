import logging
import subprocess
from datetime import datetime

_logger = logging.getLogger(__name__)


def init_logging(logger: logging.Logger, level: int = logging.INFO):
    # Clamp root logger
    logging.getLogger().setLevel(logging.WARNING)

    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.handlers[:] = []  # idempotent re-init

    # Handler for terminal output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)

    # Attach handlers to logger
    logger.addHandler(console_handler)


def set_system_time(dt: datetime) -> bool:
    """Set host machine's (Raspberry Pi's) clock from datetime object. Needs `root` privileges."""
    try:
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        subprocess.run(["sudo", "date", "-s", time_str], check=True)
        return True
    except Exception:
        _logger.exception("Failed to set system time")
        return False
