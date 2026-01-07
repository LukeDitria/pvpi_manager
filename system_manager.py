import serial
import time as pytime
from datetime import datetime, time, timedelta
import os
import argparse
import logging
import signal
import sys

from pvpi_manager import PvPiManager

# ---------------------- CLI + Main ---------------------- #
def main():
    parser = argparse.ArgumentParser(description="PV PI Manager CLI")
    parser.add_argument("--port", default="/dev/ttyS0", help="Serial port to STM32")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate")
    parser.add_argument("--log_period", type=int, default=5, help="Measurement interval (minutes)")
    parser.add_argument("--shutdown_time", type=str, default="22:00", help="Shutdown time in HH:MM")
    parser.add_argument("--off_delay", type=int, default=20, help="Shutdown delay (seconds)")
    parser.add_argument("--low_bat_volt", type=float, default=12.5, help="Shutdown voltage")
    parser.add_argument("--wakeup_time", type=str, default="08:00", help="Wakeup alarm in HH:MM")
    parser.add_argument("--log", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    parser.add_argument("--schedule_time", action='store_true', help="Use the shutdown and wakeup time")
    parser.add_argument("--enable_watchdog", action='store_true', help="Enable the power watchdog")
    parser.add_argument("--time_pi2mcu", action='store_true', help="Set MCU time from system time")
    parser.add_argument("--time_mcu2pi", action='store_true', help="Set system time from MCU")

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    shutdown_time_hour, shutdown_time_min = map(int, args.shutdown_time.split(":"))
    alarm_hour, alarm_min = map(int, args.wakeup_time.split(":"))

    shutdown_time = time(shutdown_time_hour, shutdown_time_min)
    wakeup_alarm = time(alarm_hour, alarm_min)

    logging.info(f"Shutdown Time: {shutdown_time.strftime('%H:%M:%S')}")
    logging.info(f"Wakeup Time: {wakeup_alarm.strftime('%H:%M:%S')}")

    pvpi = None
    interrupted = False

    try:
        pvpi = PvPiManager(port=args.port, baudrate=args.baud)
        logging.info("Checking connection...")
        logging.info(f"Alive: {pvpi.get_alive()}")
        
        _ = pvpi.get_mcu_time()
        
        if args.time_mcu2pi:
            pvpi.set_system_time()

        if args.time_pi2mcu:
            pvpi.set_mcu_time()

        #Start delay
        logging.info(f"30s Startup delay")
        pytime.sleep(30)
        logging.info(f"#############")
        logging.info(f"Starting...")
        logging.info(f"Log period: {args.log_period} minutes")
        logging.info(f"Watchdog: {'On' if args.enable_watchdog else 'Off'}")
        logging.info(f"Time Schedule: {'On' if args.schedule_time else 'Off'}")

        if args.enable_watchdog:
            pvpi.set_watchdog(2 * args.log_period)

        prev_time = datetime.now() - timedelta(hours=1)
        while True:
            curr_time = datetime.now()
            if curr_time.time() >= shutdown_time and args.schedule_time:
                logging.info(f"Shutdown Time!")
                break
            
            if (curr_time - prev_time).seconds >= args.log_period * 60:
                prev_time = datetime.now()

                logging.info(f"#############")
                logging.info(f"Alive: {pvpi.get_alive()}")

                pvpi.get_mcu_time()
                logging.info(f"System time: {datetime.now().strftime('%y-%m-%d %H:%M:%S')}")

                bat_v = pvpi.get_battery_voltage()
                bat_c = pvpi.get_battery_current()
                pv_v = pvpi.get_pv_voltage()
                pv_c = pvpi.get_pv_current()
                temperature = pvpi.get_board_temp()

                logging.info(f"Battery: {bat_v} V, {bat_c} A")
                logging.info(f"PV: {pv_v} V, {pv_c} A")
                logging.info(f"PV PI Temp: {temperature}C")

                if bat_v <= args.low_bat_volt:
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
            if args.schedule_time:
                pvpi.set_alarm(wakeup_alarm)

            pvpi.stop_watchdog()
            pvpi.power_off(args.off_delay)
            logging.info("SHUTDOWN NOW")
            pytime.sleep(1)
            os.system("sudo shutdown now")
            while True:
                pytime.sleep(100)

if __name__ == "__main__":
    main()
