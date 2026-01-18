import logging
import os
import sys
import time
from datetime import datetime, timedelta

from pvpi.client import PvPiClient
from pvpi.config import PvPiConfig
from pvpi.csv_logger import DailyCSVLogger
from pvpi.transports import ZmqSerialProxyInterface
from pvpi.utils import set_system_time

_logger = logging.getLogger(__name__)


def main(config: PvPiConfig):
    serial_interface = ZmqSerialProxyInterface()
    # TODO error handling

    client = PvPiClient(interface=serial_interface)

    # Check Pv Pi status
    is_alive = client.get_alive()
    _logger.info("Alive: %s", is_alive)

    # Set one clock to match the other
    if config.time_mcu2pi:
        mcu_time: datetime = client.get_mcu_time()
        set_system_time(mcu_time)
    if config.time_pi2mcu:
        client.set_mcu_time()

    # Setup CSV logger
    stats_data_logger: DailyCSVLogger | None = None
    if config.log_pvpi_stats:
        _logger.info("Logging PV PI statistics")
        stats_data_logger = DailyCSVLogger(config.data_log_path, config.keep_for_days)  # TODO

    # Delay start
    if config.startup_delay:
        _logger.info("%is Startup delay", config.startup_delay)
        time.sleep(config.startup_delay)

    _logger.info("Log period: %i minutes", config.log_period)
    _logger.info(f"Time Schedule: {'On' if config.schedule_time else 'Off'}")

    # Setup power watchdog
    _logger.info(f"Watchdog: {'On' if config.enable_watchdog else 'Off'}")
    if config.enable_watchdog:
        client.set_watchdog(2 * config.log_period)

    # Pv Pi Logging loop
    try:
        prev_time = datetime.now() - timedelta(hours=1)  # TODO set based on log-period
        while True:
            curr_time = datetime.now()
            if curr_time.time() >= config.shutdown_time and config.schedule_time:
                _logger.info("Shutdown Time!")
                break

            log_period_sec = config.log_period * 60
            sec_since_last_log = (curr_time - prev_time).seconds
            if sec_since_last_log >= log_period_sec:
                prev_time = datetime.now()

                is_alive = client.get_alive()
                mcu_time = client.get_mcu_time()
                _logger.info("Alive: %s", is_alive)
                _logger.info("Current MCU time: %s", mcu_time)
                _logger.info("System time: %s", datetime.now().strftime("%y-%m-%d %H:%M:%S"))

                bat_v = client.get_battery_voltage()
                bat_c = client.get_battery_current()
                pv_v = client.get_pv_voltage()
                pv_c = client.get_pv_current()
                temperature = client.get_board_temp()
                _logger.info("Battery: %s V, %s A", bat_v, bat_c)
                _logger.info("PV: %s V, %s A", pv_v, pv_c)
                _logger.info("PV PI Temp: %sC", temperature)

                if stats_data_logger:
                    stats_data_logger.log_stats(bat_v, bat_c, pv_v, pv_c, temperature)

                if bat_v <= config.low_bat_volt:
                    _logger.info("Shutdown Voltage!")
                    break

            time.sleep(30)
    except Exception as err:
        _logger.warning("Exception raised %s", err)
        client.stop_watchdog()
        serial_interface.close()
        sys.exit(-1)
    else:
        if config.schedule_time:
            client.set_alarm(config.wakeup_time)

        client.stop_watchdog()
        client.power_off(config.off_delay)  # TODO what?

        _logger.info("shutting down...")
        time.sleep(1)
        os.system("sudo shutdown now")  # TODO
        while True:
            _logger.info("sleeping, waiting for shutdown...")
            time.sleep(100)
