import serial
import time
from datetime import datetime, timedelta
import os


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
            time.sleep(2)  # Give MCU time to reset after opening
            print(f"[INFO] Connected to STM32 on {self.port} @ {self.baudrate} baud")
        except serial.SerialException as e:
            raise ConnectionError(f"Failed to open serial port {self.port}: {e}")

    def disconnect(self):
        """Close the serial connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[INFO] Serial connection closed")

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
        resp =  self._send_command("GET_ALIVE")

        if resp == "ALIVE":
            return True
        else:
            return False

    def get_battery_voltage(self):
        """Read battery voltage."""
        resp =  self._send_command("GET_BAT_V")

        if resp.split(",")[0] == "MILLIVOLTS":
            voltage = int(resp.split(",")[1])/1000
            return voltage
        else:
            print(f"[INFO] Failed to get Battery Voltage!")
            return None

    def get_battery_current(self):
        """Read battery current."""
        resp =  self._send_command("GET_BAT_C")

        if resp.split(",")[0] == "MILLIAMPS":
            current = int(resp.split(",")[1])/1000
            return current
        else:
            print(f"[INFO] Failed to get Charge Current!")
            return None

    def get_pv_voltage(self):
        """Read PV (solar) voltage."""
        resp =  self._send_command("GET_PV_V")

        if resp.split(",")[0] == "MILLIVOLTS":
            voltage = int(resp.split(",")[1])/1000
            return voltage
        else:
            print(f"[INFO] Failed to get PV Voltage!")
            return None

    def get_pv_current(self):
        """Read PV (solar) current."""
        resp =  self._send_command("GET_PV_C")

        if resp.split(",")[0] == "MILLIAMPS":
            current = int(resp.split(",")[1])/1000
            return current
        else:
            print(f"[INFO] Failed to get PV Current!")
            return None

    def set_watchdog(self, watchdog_period):
        """Set the Power watchdog!"""
        cmd = f"WATCHDOG_ON,{watchdog_period}"

        resp = self._send_command(cmd)
        cmd_echo = resp.split(",")[0]
        cmd_state = resp.split(",")[1]

        if cmd_state == "OK":
            print(f"[INFO] STM32 Watchdog set with period: {watchdog_period}")
            return True
        else:
            print(f"[INFO] Failed to set Watchdog! {resp}")
            return False

    def stop_watchdog(self):
        """Stop the Power watchdog!"""
        resp = self._send_command("WATCHDOG_OFF")
        cmd_echo = resp.split(",")[0]
        cmd_state = resp.split(",")[1]

        if cmd_state == "OK":
            print(f"[INFO] STM32 Watchdog OFF")
            return True
        else:
            print(f"[INFO] Failed to Stop Watchdog!")
            return False

    # ---------------------- Time Sync Commands ---------------------- #
    def set_mcu_time(self):
        """Send current system time to STM32 RTC."""
        now = datetime.now()
        cmd = f"SET_TIME,{now.year % 100},{now.month},{now.day},{now.hour},{now.minute},{now.second}"
        resp = self._send_command(cmd)
        print(f"[INFO] Set MCU to System time: {now.strftime('%y-%m-%d %H:%M:%S')}")
        return resp
    
    def set_system_time(self):
        """
        Set the system clock to match the MCU RTC.
        """
        dt = self.get_mcu_time()
        try:
            # Update system clock (requires sudo privileges)
            os.system(f"sudo date -s '{dt.strftime('%Y-%m-%d %H:%M:%S')}'")
            print("[INFO] System time updated from MCU RTC")
            return True
        except Exception as e:
            print(f"[WARN] Failed to set device time: {e}")
            return False

    def get_mcu_time(self):
        """
        Get RTC time from STM32 and return datetime.
        Expected STM32 response: 'YY,MM,DD,HH,MM,SS'
        """
        resp = self._send_command("GET_TIME")
        if not resp:
            return False

        if not resp.split(",")[0] == "GET_TIME":
            return False
        
        try:
            y, m, d, H, M, S = map(int, resp.split(",")[1:])
            full_year = 2000 + y
            dt = datetime(full_year, m, d, H, M, S)
            print(f"[INFO] STM32 RTC time: {dt}")
            return dt
        except Exception as e:
            print(f"[WARN] Failed to parse STM32 time response '{resp}': {e}")
            return None

    def set_alarm(self, alarm_time: datetime):
        """
        Set STM32 alarm using a datetime object.
        Only hour, minute, second are used.
        """
        cmd = f"SET_ALARM,{alarm_time.hour},{alarm_time.minute},{alarm_time.second}"
        resp =  self._send_command(cmd)

        if resp == "OK":
            print(f"[INFO] STM32 Alarm Set at: {alarm_time}")
            return True
        else:
            print(f"[INFO] Failed to set alarm!")
            return False

    def power_off(self, delay_s=30):
        """Schedule power-off after delay (seconds)."""
        resp = self._send_command(f"POWER_OFF,{delay_s}")
        cmd_echo = resp.split(",")[0]
        cmd_state = resp.split(",")[1]

        if cmd_state == "OK":
            print(f"[INFO] System Power OFF in {delay_s} seconds")
            return True
        else:
            print(f"[INFO] Failed to Set Power off!")
            return False

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# ---------------------- Example Usage ---------------------- #
if __name__ == "__main__":
    try:
        pvpi = PvPiManager(port="/dev/ttyAMA0")
        print("Checking connection...")
        print("Response:", pvpi.get_alive())

        print("\n--- Sync Time ---")
        pvpi.set_mcu_time()       # Set MCU time from Pi
        # pvpi.set_system_time() # Set Pi time from MCU

        print("\n--- Battery ---")
        print(f"Voltage: {pvpi.get_battery_voltage()}V")
        print(f"Current: {pvpi.get_battery_current()}A")

        print("\n--- PV (Solar) ---")
        print(f"Voltage: {pvpi.get_pv_voltage()}V")
        print(f"Current: {pvpi.get_pv_current()}A")

        future_alarm = datetime.now() + timedelta(minutes=2)
        pvpi.set_alarm(future_alarm)

        # pvpi.stop_watchdog()
        # pvpi.set_watchdog(2)
        pvpi.power_off(10)
        os.system(f"sudo shutdown now")

    except Exception as e:
        print(f"[ERROR] {e}")
