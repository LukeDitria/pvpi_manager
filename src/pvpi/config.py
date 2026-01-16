from datetime import time
from pathlib import Path
import json

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    JsonConfigSettingsSource,
)


CONFIG_PATH = Path("config.json")

class PvPiConfig(BaseSettings):
    log_period: int = 5
    off_delay: int = 20
    startup_delay: int = 20
    low_bat_volt: float = 12.5

    schedule_time: bool = False
    shutdown_time: time = time(22, 0)
    wakeup_time: time = time(8, 0)

    uart_port: str = "/dev/ttyAMA0"

    log_pvpi_stats: bool = False
    data_log_path: str = "logs"
    log_last_days: int = 7

    enable_watchdog: bool = False

    time_pi2mcu: bool = False
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