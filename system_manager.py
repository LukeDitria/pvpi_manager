import serial
import time as pytime
from datetime import datetime, time, timedelta
import os
import logging
import signal
import sys
import utils

from pvpi_client import PvPiNode
from pvpi_config import AppConfig

def main():

    config = AppConfig()
    config.write_default_config()

    logging.basicConfig(
        level=getattr(logging, "INFO", logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    shutdown_time = config.shutdown_time
    wakeup_alarm = config.wakeup_time

    logging.info(f"Shutdown Time: {shutdown_time.strftime('%H:%M:%S')}")
    logging.info(f"Wakeup Time: {wakeup_alarm.strftime('%H:%M:%S')}")

    pvpi = None
    interrupted = False

    try:
        logging.info(f"Wait for UART server startup")
        pytime.sleep(5)

        pvpi = PvPiNode()
        logging.info("Checking connection...")
        logging.info(f"Alive: {pvpi.get_alive()}")
        
        _ = pvpi.get_mcu_time()
        
        if config.time_mcu2pi:
            pvpi.set_system_time()

        if config.time_pi2mcu:
            pvpi.set_mcu_time()

        if config.log_pvpi_stats:
            logging.info(f"Logging PV PI statistics")
            stats_data_logger = utils.DailyCSVLogger(config.data_log_path, config.log_last_days)

        #Start delay
        logging.info(f"20s Startup delay")
        pytime.sleep(20)
        logging.info(f"######STARTING#######")
        logging.info(f"Log period: {config.log_period} minutes")
        logging.info(f"Watchdog: {'On' if config.enable_watchdog else 'Off'}")
        logging.info(f"Time Schedule: {'On' if config.schedule_time else 'Off'}")

        if config.enable_watchdog:
            pvpi.set_watchdog(2 * config.log_period)

        prev_time = datetime.now() - timedelta(hours=1)
        
        logging.info(f"######BEGIN#######")
        while True:
            curr_time = datetime.now()
            if curr_time.time() >= shutdown_time and config.schedule_time:
                logging.info(f"Shutdown Time!")
                break
            
            if (curr_time - prev_time).seconds >= config.log_period * 60:
                prev_time = datetime.now()

                logging.info(f"#############")
                logging.info(f"Alive: {pvpi.get_alive()}")

                logging.info(f"Current MCU time: {pvpi.get_mcu_time()}")
                logging.info(f"System time: {datetime.now().strftime('%y-%m-%d %H:%M:%S')}")

                bat_v = pvpi.get_battery_voltage()
                bat_c = pvpi.get_battery_current()
                pv_v = pvpi.get_pv_voltage()
                pv_c = pvpi.get_pv_current()
                temperature = pvpi.get_board_temp()

                logging.info(f"Battery: {bat_v} V, {bat_c} A")
                logging.info(f"PV: {pv_v} V, {pv_c} A")
                logging.info(f"PV PI Temp: {temperature}C")

                if config.log_pvpi_stats:
                    stats_data_logger.log_stats(
                        bat_v, bat_c,
                        pv_v, pv_c,
                        temperature
                    )

                if bat_v <= config.low_bat_volt:
                    logging.info(f"Shutdown Voltage!")
                    break

            pytime.sleep(30)

    except KeyboardInterrupt:
        """Handle Ctrl+C or SIGTERM cleanly."""
        logging.warning("Interrupt received — cleaning up...")
        if pvpi:
            pvpi.stop_watchdog()
            pvpi.disconnect()
            interrupted = True
        logging.info("Exiting safely.")
        exit

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        """Handle Ctrl+C or SIGTERM cleanly."""
        logging.warning("Interrupt received — cleaning up...")
        if pvpi:
            pvpi.stop_watchdog()
            pvpi.disconnect()
            interrupted = True
        logging.info("Exiting safely.")
        exit

    finally:
       if not interrupted:
            if config.schedule_time:
                pvpi.set_alarm(wakeup_alarm)

            pvpi.stop_watchdog()
            pvpi.power_off(config.off_delay)
            logging.info("SHUTDOWN NOW")
            pytime.sleep(1)
            os.system("sudo shutdown now")
            while True:
                pytime.sleep(100)

if __name__ == "__main__":
    main()
