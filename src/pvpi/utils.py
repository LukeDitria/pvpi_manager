import logging
import os
import platform
import subprocess
import sys
from datetime import datetime

_logger = logging.getLogger(__name__)


def set_system_time(dt: datetime) -> bool:
    """Set host machine's (Raspberry Pi's) clock from datetime object. Needs `root` privileges."""
    try:
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        subprocess.run(["sudo", "date", "-s", time_str], check=True)
        return True
    except Exception:
        _logger.exception("Failed to set system time")
        return False


def is_linux() -> bool:
    # fast path
    if sys.platform.startswith("linux"):
        return True

    # paranoia tier
    return os.name == "posix" and platform.system() == "Linux"
