import serial
import time as pytime
from datetime import datetime, time
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
    args = parser.parse_args()

    pvpi = PvPiManager(port=args.port, baudrate=args.baud)
    logging.info("Checking connection...")
    logging.info(f"Alive: {pvpi.get_alive()}")
    pvpi.set_mcu_time()
    print(pvpi.get_mcu_time())

if __name__ == "__main__":
    main()
