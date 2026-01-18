import logging
import shutil
import subprocess
from importlib import resources
from pathlib import Path

_SERVICES = ["pvpi_manager.service", "pvpi_uart.service"]

_logger = logging.getLogger(__name__)


def install_systemd(*, user: bool = True) -> None:
    _logger.info("Install systemd services as %s", "user" if user else "root")
    if user:
        target_dir = Path.home() / ".config/systemd/user"
        systemctl = ["systemctl", "--user"]
    else:
        target_dir = Path("/etc/systemd/system")
        systemctl = ["systemctl"]

    # Copy service files to systemd
    target_dir.mkdir(parents=True, exist_ok=True)
    pkg = resources.files("pvpi").joinpath("systemd")
    for name in _SERVICES:
        src = pkg.joinpath(name)
        dst = target_dir / name
        with resources.as_file(src) as fsrc:
            shutil.copyfile(fsrc, dst)

    # Start systemd services
    subprocess.run(systemctl + ["daemon-reload"], check=True)
    for name in _SERVICES:
        subprocess.run(systemctl + ["enable", name], check=True)
        subprocess.run(systemctl + ["start", name], check=True)
        _logger.info("%s installed & started", name)
    _logger.info("Installation complete!")
