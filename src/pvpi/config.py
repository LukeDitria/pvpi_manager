import json
import pathlib
from datetime import time
from pathlib import Path

from platformdirs import user_data_dir
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
)

from pvpi.utils import default_uart_port


class PvPiConfig(BaseSettings, extra="forbid"):
    uart_port: str = Field(default_factory=default_uart_port, description="UART port path")

    log_period: int = Field(5, description="Pv Pi system metrics logging interval minutes", gt=0)  # mins
    startup_delay: int = Field(20, description="Seconds delay after service start before proceeding", ge=0)  # secs

    low_bat_volt: float = Field(12.5, description="Voltage at which to shutdown the Raspberry Pi", ge=0)  # volts
    wake_up_volt: float = Field(12.5, description="Voltage at which power supply will be turned on", ge=0)  # volts

    # Turning the power supply off on shutdown
    power_off_on_shutdown: bool = Field(True, description="Turn off power supply on shutdown")
    power_off_delay: int = Field(20, description="Seconds delay after shutdown to turn off power supply", ge=0)

    # Wakeup & Shutdown times
    schedule_time: bool = Field(False, description="Enable scheduled shutdown and wakeup")
    shutdown_time: time = time(22, 0)  # TODO
    wakeup_time: time = time(8, 0)  # TODO

    # Enable CSV logging of voltages, currents, and temperatures
    log_pvpi_stats: bool = Field(True, description="Enable CSV logging of Pv Pi metrics")
    data_log_path: Path = Field(
        default_factory=lambda: Path(user_data_dir("pvpi")), description="Pv Pi CSV log file path"
    )
    keep_for_days: int = Field(7, description="Num of days logging to retain")

    # Watchdog
    enable_watchdog: bool = Field(False, description="Enable power watchdog")
    watchdog_period_mins: int = Field(2, description="Watchdog inspection interval in minutes", gt=0)
    disable_watchdog_on_shutdown: bool = Field(True, description="Disable power watchdog during shutdown")

    # Clocks
    time_pi2mcu: bool = Field(False, description="Set Pv Pi's MCU clock to match Raspberry Pi's clock on boot")
    time_mcu2pi: bool = Field(False, description="Set Raspberry Pi's clock to match Pv Pi's MCU clock on boot")

    @classmethod
    def from_file(cls, path: str | None = None):
        if path is None:
            return cls()
        ext = pathlib.Path(path).suffix
        if ext == ".json":
            config_path = Path(path)
            if config_path.exists():
                with open(path) as f:
                    return cls.model_validate(json.load(f))
            else:
                config_path.parent.mkdir(parents=True, exist_ok=True)
                data = cls().model_dump(mode='json')
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                return cls

        raise ValueError(f"unsupported file type '{ext}'")
