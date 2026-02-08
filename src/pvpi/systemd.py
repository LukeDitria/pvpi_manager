import logging
import os
import pwd
import subprocess
import sys
from pathlib import Path

from pvpi.utils import is_linux

_SERVICES = ["pvpi_uart.service", "pvpi_manager.service"]

_logger = logging.getLogger(__name__)


def _get_user_info() -> tuple[str, Path]:
    """Return (username, home_dir) for the real (non-root) user."""
    username = os.environ.get("SUDO_USER") or os.getlogin()
    home = Path(pwd.getpwnam(username).pw_dir)
    return username, home


def _render_service(name: str, user: str, home: Path) -> str:
    """Generate a systemd unit file with the correct user and paths."""
    project_dir = home / "pvpi_manager"
    uv = home / ".local/bin/uv"

    if name == "pvpi_uart.service":
        return (
            "[Unit]\n"
            "Description=UART server for communication with the PV PI\n"
            "After=network-online.target\n"
            "Wants=network-online.target\n"
            "\n"
            "[Service]\n"
            "Type=simple\n"
            f"User={user}\n"
            f"Group={user}\n"
            f"WorkingDirectory={project_dir}\n"
            f"ExecStartPre={uv} sync --frozen --no-dev\n"
            f"ExecStart={uv} run pvpi uart-proxy\n"
            "Restart=always\n"
            "RestartSec=10\n"
            "\n"
            "[Install]\n"
            "WantedBy=default.target\n"
        )

    if name == "pvpi_manager.service":
        return (
            "[Unit]\n"
            "Description=PV PI Manager Service\n"
            "After=pvpi_uart.service\n"
            "Requires=pvpi_uart.service\n"
            "\n"
            "[Service]\n"
            "Type=simple\n"
            f"User={user}\n"
            f"Group={user}\n"
            f"WorkingDirectory={project_dir}\n"
            f"ExecStartPre={uv} sync --frozen --no-dev\n"
            f"ExecStart={uv} run pvpi manager\n"
            "Restart=always\n"
            "RestartSec=10\n"
            "\n"
            "[Install]\n"
            "WantedBy=multi-user.target\n"
        )

    raise ValueError(f"unknown service: {name}")


def _check(home: Path):
    if not is_linux():
        raise OSError("System is not linux")
    if os.geteuid() != 0:
        _logger.warning("sudo required")
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)
    project_dir = home / "pvpi_manager"
    if not project_dir.exists():
        _logger.error("Expected project files at %s - see readme", project_dir)
        sys.exit(1)


def install_systemd() -> None:
    user, home = _get_user_info()
    _check(home)

    _logger.info("Installing systemd services for user '%s'", user)
    target_dir = Path("/etc/systemd/system")
    target_dir.mkdir(parents=True, exist_ok=True)

    for name in _SERVICES:
        (target_dir / name).write_text(_render_service(name, user, home))

    # Start systemd services
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    for name in _SERVICES:
        subprocess.run(["systemctl", "enable", name], check=True)
        subprocess.run(["systemctl", "restart", name], check=True)
        _logger.info("%s installed & started", name)
    _logger.info("Installation complete!")


def uninstall_systemd() -> None:
    _, home = _get_user_info()
    _check(home)
    target_dir = Path("/etc/systemd/system")
    for name in _SERVICES:
        subprocess.run(["systemctl", "disable", name], check=True)
        dst = target_dir / name
        os.remove(dst)
        _logger.info("%s uninstalled", name)
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    _logger.info("Uninstall complete!")
