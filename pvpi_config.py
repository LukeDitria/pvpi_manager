from datetime import time
from pathlib import Path
import json

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    JsonConfigSettingsSource,
)


CONFIG_PATH = Path("config.json")

class AppConfig(BaseSettings):

    # UART Port path
    uart_port: str = "/dev/ttyAMA0"

    # Data logging period 
    log_period: int = 5

    # Add delay at start to allow for disabling of service
    startup_delay: int = 20

    # What voltage to shutdown the Pi at
    low_bat_volt: float = 12.5

    # Power supply will be turned back on at this voltage
    wake_up_voltage: int = 13

    # Turning the power supply off on shutdown 
    power_off_on_shutdown: bool = True
    power_off_delay: int = 20

    # Enabling wakeup and shutdown times
    schedule_time: bool = False
    shutdown_time: time = time(22, 0)
    wakeup_time: time = time(8, 0)

    # Enable CSV logging of Voltages, Currents and temp
    log_pvpi_stats: bool = False
    data_log_path: str = "logs"
    log_last_days: int = 7

    # Enable and config the power watchdog
    enable_watchdog: bool = False
    watchdog_period_mins: int = 2
    disable_watchdog_on_shutdown: bool = True

    # Set the MCU time to the System time every boot up
    time_pi2mcu: bool = False

    # Set the System time to the PV PI time every boot up
    time_mcu2pi: bool = False

    model_config = SettingsConfigDict(
        env_prefix="PVPI_",
        json_file=CONFIG_PATH,
        extra="ignore"

    )

    def write_default_config(self):
        if not CONFIG_PATH.exists():
            defaults = self.model_dump(mode="json")
            CONFIG_PATH.write_text(json.dumps(defaults, indent=2))

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            JsonConfigSettingsSource(settings_cls),
            env_settings,
        )