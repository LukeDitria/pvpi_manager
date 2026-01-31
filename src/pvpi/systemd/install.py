import logging
import os
import pathlib
import shutil
import subprocess
import sys
from importlib import resources
from pathlib import Path

from pvpi.utils import is_linux

_SERVICES = ["pvpi_uart.service", "pvpi_manager.service"]

_logger = logging.getLogger(__name__)


def _check():
    if not is_linux():
        raise OSError("System is not linux")
    if os.geteuid() != 0:
        _logger.warning("sudo required")
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)
    if not pathlib.Path("/home/pi/pvpi_manager").exists():
        _logger.error("pvpi install is only meant for raspi - see readme")
        sys.exit(1)


def install_systemd() -> None:
    _check()

    _logger.info("Installing systemd services")
    target_dir = Path("/etc/systemd/system")

    # Copy service files to systemd
    target_dir.mkdir(parents=True, exist_ok=True)
    pkg = resources.files("pvpi").joinpath("systemd")
    for name in _SERVICES:
        src = pkg.joinpath(name)
        dst = target_dir / name
        with resources.as_file(src) as fsrc:
            shutil.copyfile(fsrc, dst)

    # Start systemd services
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    for name in _SERVICES:
        subprocess.run(["systemctl", "enable", name], check=True)
        subprocess.run(["systemctl", "restart", name], check=True)
        _logger.info("%s installed & started", name)
    _logger.info("Installation complete!")


def uninstall_systemd() -> None:
    _check()
    target_dir = Path("/etc/systemd/system")
    for name in _SERVICES:
        subprocess.run(["systemctl", "disable", name], check=True)
        dst = target_dir / name
        os.remove(dst)
        _logger.info("%s uninstalled", name)
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    _logger.info("Uninstall complete!")
