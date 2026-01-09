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
    pvpi = PvPiManager()
    logging.info("Checking connection...")
    logging.info(f"Alive: {pvpi.get_alive()}")
    pvpi.set_mcu_time()
    print(pvpi.get_mcu_time())

if __name__ == "__main__":
    main()
