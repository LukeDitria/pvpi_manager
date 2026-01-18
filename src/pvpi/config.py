from datetime import time
from pathlib import Path
from typing import Literal

from platformdirs import user_data_dir
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
)


class PvPiConfig(BaseSettings, extra="forbid"):
    log_period: int = Field(5, description="Minutes between logging Pv Pi system metrics")
    off_delay: int = Field(20, description="")
    startup_delay: int = Field(20, description="")
    low_bat_volt: float = Field(12.5, description="")

    schedule_time: bool = False
    shutdown_time: time = time(22, 0)
    wakeup_time: time = time(8, 0)

    uart_port: str = "/dev/ttyAMA0"

    # CSV logger todo rename
    log_pvpi_stats: bool = Field(False, description="Enable CSV logging of Pv Pi metrics")
    data_log_path: Path = Field(
        default_factory=lambda: Path(user_data_dir("pvpi")), description="Pv Pi CSV log file path"
    )
    keep_for_days: int = 7

    enable_watchdog: bool = False  # TODO explain

    # TODO:
    main_clock: Literal["pi", "mcu"] | None = Field(
        None,
        description="Set main clock to either Raspberry Pi or Pv PI MCU, and set the other to match. "
        "Set config value to None to update neither's clock."
        "Setting PV Pi MCU as main clock requires root permissions to set Raspberry Pi clock to match.",
    )
    time_pi2mcu: bool = Field(False, description="Set Pv Pi's MCU clock to match Raspberry Pi's clock")
    time_mcu2pi: bool = Field(False, description="Set Raspberry Pi's clock to match Pv Pi's MCU clock")
