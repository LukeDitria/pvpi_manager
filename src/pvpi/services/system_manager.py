import logging
import os
import time
from datetime import datetime, timedelta

from pvpi.client import PvPiClient
from pvpi.config import PvPiConfig
from pvpi.logging_ import RotatingCSVLogger
from pvpi.transports import ZmqSerialProxyInterface
from pvpi.utils import set_system_time

_logger = logging.getLogger(__name__)


def run(config: PvPiConfig):
    serial_interface = ZmqSerialProxyInterface()
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
    stats_data_logger: RotatingCSVLogger | None = None
    if config.log_pvpi_stats:
        _logger.info("Logging PV PI statistics to %s", config.data_log_path)
        stats_data_logger = RotatingCSVLogger(config.data_log_path, config.keep_for_days)

    # Delay start
    if config.startup_delay:
        _logger.info("%is Startup delay", config.startup_delay)
        time.sleep(config.startup_delay)

    _logger.info("Log period: %i minutes", config.log_period)
    _logger.info("Time Schedule: %s", "On" if config.schedule_time else "Off")

    # Setup power watchdog
    _logger.info("Watchdog: %s", "On" if config.enable_watchdog else "Off")
    if config.enable_watchdog:
        client.set_watchdog(config.watchdog_period_mins)
        # Make sure watchdog is reset twice every watchdog period
        watchdog_period_sec = (config.watchdog_period_mins * 60)//2
        prev_watchdog_time = datetime.now() - timedelta(seconds=watchdog_period_sec)
        _logger.info("Watchdog polling interval set to %s min", config.watchdog_period_mins)
    else:
        client.stop_watchdog()

    client.set_wakeup_voltage(config.wake_up_volt)
    _logger.info("Wakeup Voltage set at: %sV", config.wake_up_volt)

    # Pv Pi Logging loop
    log_period_sec = config.log_period * 60
    prev_log_time = datetime.now() - timedelta(seconds=log_period_sec)

    try:
        while True:
            curr_time = datetime.now()
            if config.schedule_time:
                shutdown = config.shutdown_time
                wakeup = config.wakeup_time

                if shutdown < wakeup:
                    # Same day: shutdown window is between shutdown_time and wakeup_time
                    should_shutdown = shutdown <= curr_time.time() < wakeup
                else:
                    # Overnight: e.g. shutdown=23:00, wakeup=06:00
                    should_shutdown = curr_time.time() >= shutdown or curr_time.time() < wakeup

                if should_shutdown:
                    _logger.info("Shutdown Time!")
                    break

            if config.enable_watchdog:
                sec_since_last_wd = (curr_time - prev_watchdog_time).seconds
                if sec_since_last_wd >= watchdog_period_sec:
                    is_alive = client.get_alive()
                    _logger.info("Watchdog Alive: %s", is_alive)
                    prev_watchdog_time = datetime.now()

            sec_since_last_log = (curr_time - prev_log_time).seconds
            if sec_since_last_log >= log_period_sec:
                prev_log_time = datetime.now()

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

            time.sleep(10)
    except Exception as err:
        _logger.warning("Exception raised %s", err)
        client.stop_watchdog()
        serial_interface.close()
        raise
    else:
        _logger.info("Closing down...")
        client.stop_watchdog()
        _logger.info("Watchdog stopped")

        if config.schedule_time:
            client.set_alarm(config.wakeup_time)
            _logger.info("Alarm set %s", config.wakeup_time)
        if config.power_off_on_shutdown:
            client.power_off(delay_s=config.power_off_delay)
            _logger.info("Powering off Pv Pi")

        _logger.info("Shutting down...")
        time.sleep(1)
        os.system("sudo shutdown now")  # warning: requires permissions
        while True:
            _logger.info("sleeping, waiting for shutdown...")
            time.sleep(100)
