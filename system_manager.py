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

class SystemManager:
    def __init__(self):
        self.config = AppConfig()
        self.config.write_default_config()

        logging.basicConfig(
            level=getattr(logging, "INFO", logging.INFO),
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        if self.config.schedule_time:
            logging.info(f"Shutdown Time: {self.config.shutdown_time.strftime('%H:%M:%S')}")
            logging.info(f"Wakeup Time: {self.config.wakeup_time.strftime('%H:%M:%S')}")

        self.interrupted = False

        logging.info(f"Wait for UART server startup")
        pytime.sleep(5)

        self.pvpi = PvPiNode()

    def setup(self):
        logging.info("Checking connection...")
        logging.info(f"Alive: {self.pvpi.get_alive()}")

        if self.config.time_mcu2pi:
            self.pvpi.set_system_time()

        if self.config.time_pi2mcu:
            self.pvpi.set_mcu_time()

        if self.config.log_pvpi_stats:
            logging.info(f"Logging PV PI statistics")
            self.stats_data_logger = utils.DailyCSVLogger(
                self.config.data_log_path, 
                self.config.log_last_days)

        #Start delay
        logging.info(f"{self.config.startup_delay}s Startup delay")
        pytime.sleep(self.config.startup_delay)
        logging.info(f"######STARTING#######")
        logging.info(f"Log period: {self.config.log_period} minutes")
        logging.info(f"Watchdog: {'On' if self.config.enable_watchdog else 'Off'}")
        logging.info(f"Time Schedule: {'On' if self.config.schedule_time else 'Off'}")

        if self.config.enable_watchdog:
            self.pvpi.set_watchdog(2 * self.config.log_period)


    def run_manager(self):
        try:
            logging.info(f"######BEGIN#######")
            prev_time = datetime.now() - timedelta(hours=1)
            while True:
                curr_time = datetime.now()
                if curr_time.time() >= self.config.shutdown_time and self.config.schedule_time:
                    logging.info(f"Shutdown Time!")
                    break
                
                if (curr_time - prev_time).seconds >= self.config.log_period * 60:
                    prev_time = datetime.now()

                    logging.info(f"#############")
                    logging.info(f"Alive: {self.pvpi.get_alive()}")

                    logging.info(f"Current MCU time: {self.pvpi.get_mcu_time()}")
                    logging.info(f"System time: {datetime.now().strftime('%y-%m-%d %H:%M:%S')}")

                    bat_v = self.pvpi.get_battery_voltage()
                    bat_c = self.pvpi.get_battery_current()
                    pv_v = self.pvpi.get_pv_voltage()
                    pv_c = self.pvpi.get_pv_current()
                    temperature = self.pvpi.get_board_temp()

                    logging.info(f"Battery: {bat_v} V, {bat_c} A")
                    logging.info(f"PV: {pv_v} V, {pv_c} A")
                    logging.info(f"PV PI Temp: {temperature}C")

                    if self.config.log_pvpi_stats:
                        self.stats_data_logger.log_stats(
                            bat_v, bat_c,
                            pv_v, pv_c,
                            temperature
                        )

                    if bat_v <= self.config.low_bat_volt:
                        logging.info(f"Shutdown Voltage!")
                        break

                pytime.sleep(30)

        except KeyboardInterrupt:
            """Handle Ctrl+C or SIGTERM cleanly."""
            logging.warning("Interrupt received — cleaning up...")
            if self.pvpi:
                self.pvpi.stop_watchdog()
                self.pvpi.disconnect()
                self.interrupted = True
            logging.info("Exiting safely.")
            exit

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            """Handle Ctrl+C or SIGTERM cleanly."""
            logging.warning("Interrupt received — cleaning up...")
            if self.pvpi:
                self.pvpi.stop_watchdog()
                self.pvpi.disconnect()
                self.interrupted = True
            logging.info("Exiting safely.")
            exit
        finally:
            if not self.interrupted:
                if self.config.schedule_time:
                    self.pvpi.set_alarm(self.config.wakeup_alarm)

                self.pvpi.stop_watchdog()
                self.pvpi.power_off(config.off_delay)
                logging.info("SHUTDOWN NOW")
                pytime.sleep(1)
                os.system("sudo shutdown now")
                while True:
                    pytime.sleep(100)

def main():
    sys_manager = SystemManager()
    sys_manager.setup()
    sys_manager.run_manager()


if __name__ == "__main__":
    main()
