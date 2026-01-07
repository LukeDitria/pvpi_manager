import serial
import time as pytime
from datetime import datetime, time
import os
import argparse
import logging
import signal
import sys


class PvPiManager:
    """High-level UART interface for communicating with the PV PI"""

    def __init__(self, port="/dev/ttyS0", baudrate=115200, timeout=2):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.connect()

    # ---------------------- Connection Management ---------------------- #
    def connect(self):
        """Open the serial connection to the STM32."""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            pytime.sleep(2)  # Give MCU time to reset after opening
            logging.info(f"Connected to STM32 on {self.port} @ {self.baudrate} baud")
        except serial.SerialException as e:
            raise ConnectionError(f"Failed to open serial port {self.port}: {e}")

    def disconnect(self):
        """Close the serial connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            logging.info("Serial connection closed")

    # ---------------------- Command Interface ---------------------- #
    def _send_command(self, command, expect_response=True):
        """Send a command and return the STM32's response if available."""
        if not self.ser or not self.ser.is_open:
            raise ConnectionError("Serial port not open")

        cmd = command.strip() + "\n"
        self.ser.write(cmd.encode("utf-8"))

        if not expect_response:
            return None

        response = self.ser.readline().decode("utf-8").strip()
        return response

    # ---------------------- Helper Commands ---------------------- #
    def get_alive(self):
        """Check if STM32 is responsive."""
        resp = self._send_command("GET_ALIVE")
        return resp == "ALIVE"

    def get_battery_voltage(self):
        """Read battery voltage."""
        resp = self._send_command("GET_BAT_V")

        if resp.split(",")[0] == "MILLIVOLTS":
            voltage = int(resp.split(",")[1]) / 1000
            return voltage
        else:
            logging.warning("Failed to get Battery Voltage!")
            return None

    def get_battery_current(self):
        """Read battery current."""
        resp = self._send_command("GET_BAT_C")

        if resp.split(",")[0] == "MILLIAMPS":
            current = int(resp.split(",")[1]) / 1000
            return current
        else:
            logging.warning("Failed to get Charge Current!")
            return None

    def get_pv_voltage(self):
        """Read PV (solar) voltage."""
        resp = self._send_command("GET_PV_V")

        if resp.split(",")[0] == "MILLIVOLTS":
            voltage = int(resp.split(",")[1]) / 1000
            return voltage
        else:
            logging.warning("Failed to get PV Voltage!")
            return None

    def get_pv_current(self):
        """Read PV (solar) current."""
        resp = self._send_command("GET_PV_C")

        if resp.split(",")[0] == "MILLIAMPS":
            current = int(resp.split(",")[1]) / 1000
            return current
        else:
            logging.warning("Failed to get PV Current!")
            return None

    def set_watchdog(self, watchdog_period):
        """Set the Power watchdog."""
        cmd = f"WATCHDOG_ON,{watchdog_period}"
        resp = self._send_command(cmd)
        cmd_state = resp.split(",")[1] if "," in resp else "FAIL"

        if cmd_state == "OK":
            logging.info(f"STM32 Watchdog set with period: {watchdog_period}")
            return True
        else:
            logging.warning(f"Failed to set Watchdog! Response: {resp}")
            return False

    def stop_watchdog(self):
        """Stop the Power watchdog."""
        try:
            resp = self._send_command("WATCHDOG_OFF")
            cmd_state = resp.split(",")[1] if "," in resp else "FAIL"

            if cmd_state == "OK":
                logging.info("STM32 Watchdog OFF")
                return True
            else:
                logging.warning("Failed to Stop Watchdog!")
                return False
        except Exception as e:
            logging.error(f"Error stopping watchdog: {e}")
            return False

    # ---------------------- Time Sync Commands ---------------------- #
    def set_mcu_time(self):
        """Send current system time to STM32 RTC."""
        now = datetime.now()
        cmd = f"SET_TIME,{now.year % 100},{now.month},{now.day},{now.hour},{now.minute},{now.second}"
        resp = self._send_command(cmd)
        logging.info(f"Set MCU to System time: {now.strftime('%y-%m-%d %H:%M:%S')}")
        return resp

    def get_board_temp(self):
        """Get the PVPI Board temperature"""
        resp = self._send_command("GET_TEMP")
        if not resp:
            return None

        if not resp.split(",")[0] == "TEMP":
            return None

        try:
            temperature = int(resp.split(",")[1])
            return temperature
        except Exception as e:
            logging.warning(f"Failed to PV PI Temperature '{resp}': {e}")
            return None

    def get_mcu_time(self):
        """Get RTC time from STM32 and return datetime."""
        resp = self._send_command("GET_TIME")
        if not resp:
            return None

        if not resp.split(",")[0] == "GET_TIME":
            return None

        try:
            y, m, d, H, M, S = map(int, resp.split(",")[1:])
            full_year = 2000 + y
            dt = datetime(full_year, m, d, H, M, S)
            logging.info(f"STM32 RTC time: {dt}")
            return dt
        except Exception as e:
            logging.warning(f"Failed to parse STM32 time response '{resp}': {e}")
            return None

    def set_system_time(self):
        """Set Raspberry Pi system clock from datetime object."""
        dt = self.get_mcu_time()
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")

        try:
            # Needs root privileges!
            subprocess.run(
                ["sudo", "date", "-s", time_str],
                check=True
            )
            return True
        except Exception as e:
            logging.error(f"Failed to set system time: {e}")
            return False

    def set_alarm(self, alarm_time: time):
        """Set STM32 alarm using a datetime time object."""
        cmd = f"SET_ALARM,{alarm_time.hour},{alarm_time.minute},{alarm_time.second}"
        resp = self._send_command(cmd)

        if resp == "OK":
            logging.info(f"STM32 Alarm Set at: {alarm_time}")
            return True
        else:
            logging.warning("Failed to set alarm!")
            return False

    def power_off(self, delay_s=30):
        """Schedule power-off after delay (seconds)."""
        resp = self._send_command(f"POWER_OFF,{delay_s}")
        cmd_state = resp.split(",")[1] if "," in resp else "FAIL"

        if cmd_state == "OK":
            logging.info(f"System Power OFF in {delay_s} seconds")
            return True
        else:
            logging.warning("Failed to Set Power off!")
            return False

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
