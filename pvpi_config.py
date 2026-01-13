from datetime import time
from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    JsonConfigSettingsSource,
)


CONFIG_PATH = Path("config.json")

class AppConfig(BaseSettings):
    log_period: int = 5
    shutdown_time: time = time(22, 0)
    off_delay: int = 20
    low_bat_volt: float = 12.5
    wakeup_time: time = time(8, 0)
    uart_port: str = "/dev/ttyAMA0"

    schedule_time: bool = False
    enable_watchdog: bool = False
    time_pi2mcu: bool = False
    time_mcu2pi: bool = False

    model_config = SettingsConfigDict(
        env_prefix="PVPI_",
        json_file=CONFIG_PATH,
        extra="ignore"

    )

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