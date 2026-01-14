import serial
import time as pytime
from datetime import datetime, time
import os
import argparse
import logging
import signal
import sys
import zmq


class PvPiManager:
    """High-level UART interface for communicating with the PV PI"""
    charge_states = [
        "Not charging",
        "Trickle Charge (VBAT < VBAT_SHORT)",
        "Pre-Charge (VBAT < VBAT_LOWV)",
        "Fast Charge (CC mode)",
        "Taper Charge (CV mode)",
        "NA",
        "Top-off Timer Charge",
        "Charge Termination Done"
    ]

    fault_states = [
        "NA"
        "DRV_SUP pin voltage",
        "Charge safety timer",
        "Thermal shutdown",
        "Battery over-voltage",
        "Battery over-current",
        "Input over-voltage",
        "Input under-voltage",
    ]


    def __init__(self, timeout=2):
        self.timeout = timeout
        self.ser = None
        self.connect()

    # ---------------------- Connection Management ---------------------- #
    def connect(self):
        """Open the connection to the UART Server."""
        # try:
        #     self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        #     pytime.sleep(2)  # Give MCU time to reset after opening
        #     logging.info(f"Connected to STM32 on {self.port} @ {self.baudrate} baud")
        # except serial.SerialException as e:
        #     raise ConnectionError(f"Failed to open serial port {self.port}: {e}")

        ZMQ_PORT = "tcp://127.0.0.1:5555"

        try:
            self.context = zmq.Context()
            logging.info("Connecting to UART server...")
            # The DEALER socket is used for asynchronous communication with a ROUTER
            self.socket = self.context.socket(zmq.DEALER)
            # Give the client a unique identity (optional but good practice)
            self.socket.setsockopt(zmq.IDENTITY, b"client_" + str(pytime.time()).encode())
            self.socket.connect(ZMQ_PORT)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to UART Server {ZMQ_PORT}: {e}")

    def disconnect(self):
        """Close the serial connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            logging.info("Serial connection closed")

    def _send_command(self, data_request):
        try:
            # Send the request
            # self.socket.send_string(data_request)
            self.socket.send_multipart([b"send_command", data_request.encode('utf-8')])
            
            # Wait for the reply from the server
            reply_parts = self.socket.recv_multipart()
            reply = reply_parts[1].decode('utf-8')
                        
            return reply

        except Exception as e:
            logging.info(f"An error occurred in the client: {e}")
            return None

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

    # ---------------------- Time Sync Commands ---------------------- #
    def set_mcu_time(self):
        """Send current system time to STM32 RTC."""
        now = datetime.now()
        cmd = f"SET_TIME,{now.year % 100},{now.month},{now.day},{now.hour},{now.minute},{now.second}"
        resp = self._send_command(cmd)
        logging.info(f"Set MCU to System time: {now.strftime('%y-%m-%d %H:%M:%S')}")
        return resp

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

    def get_charge_state_code(self):
        """Get PV PI charge state code"""
        resp = self._send_command(f"GET_CHARGE_STATE")
        cmd_state = resp.split(",")[0] if "," in resp else "FAIL"

        if cmd_state == "CHARGE_STATE":
            charge_state_code = int(resp.split(",")[1])
            return charge_state_code
        else:
            logging.warning("Failed to get charge state!")
            return None

    def get_charge_state(self):
        """Get PV PI charge state string"""
        charge_state_code = self.get_charge_state_code()
        if charge_state_code is not None:
            return self.charge_states[charge_state_code]
        else:
            return "NA"

    def get_fault_code(self):
        """Get PV PI fault code"""
        resp = self._send_command(f"GET_FAULT_CODE")
        cmd_state = resp.split(",")[0] if "," in resp else "FAIL"

        if cmd_state == "FAULT_CODE":
            fault_code = int(resp.split(",")[1])
            return fault_code
        else:
            logging.warning("Failed to get fault code!")
            return None

    def get_fault_states(self):
        """Get PV PI fault states as string"""
        fault_code = self.get_fault_code()
        if fault_code is not None:
            fault_states_list = [self.fault_states[bit] for bit in range(8) if fault_code & (1 << bit)]
            return fault_states_list
        else:
            return []

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
