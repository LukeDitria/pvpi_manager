import logging
from datetime import datetime, time
from enum import StrEnum

from pvpi.transports import BaseTransportInterface, ZmqSerialProxyInterface, SerialInterface

_logger = logging.getLogger(__name__)


class PvPiUnits(StrEnum):
    mV = "MILLIVOLTS"
    mA = "MILLIAMPS"


class PvPiChargeStates(StrEnum):
    NotCharging = "Not charging"
    TrickleCharge = "Trickle Charge (VBAT < VBAT_SHORT)"
    PreCharge = "Pre-Charge (VBAT < VBAT_LOWV)"
    FastCharge = "Fast Charge (CC mode)"
    TaperCharge = "Taper Charge (CV mode)"
    NA = "NA"
    TopOffTimerCharge = "Top-off Timer Charge"
    ChargeTerminationDone = "Charge Termination Done"


class PvPiFaultStates(StrEnum):
    NA = "NA"
    DrvSupPinVoltage = "DRV_SUP pin voltage"
    ChargeSafetyTimer = "Charge safety timer"
    ThermalShutdown = "Thermal shutdown"
    BatteryOverVoltage = "Battery over-voltage"
    BatteryOverCurrent = "Battery over-current"
    InputOverVoltage = "Input over-voltage"
    InputUnderVoltage = "Input under-voltage"


def _get_interface():
    try:
        return ZmqSerialProxyInterface()
    except Exception:
        _logger.debug("")
        pass
    return SerialInterface()


class PvPiClient:
    def __init__(self, interface: BaseTransportInterface = None):
        self._interface = interface or _get_interface()

    def get_alive(self) -> bool:
        """Return True if PV PI is responsive"""
        return self._interface.write(message=b"GET_ALIVE") == "ALIVE"

    def get_battery_voltage(self) -> float:
        """Read battery voltage (V)"""
        resp = self._interface.write(b"GET_BAT_V").decode()
        unit, value = resp.split(",")
        if unit == PvPiUnits.mV:
            return int(value) / 1000
        else:
            raise ValueError("Failed to read battery voltage")

    def get_battery_current(self) -> float:
        """Read battery current (A)"""
        resp = self._interface.write(b"GET_BAT_C").decode()
        unit, value = resp.split(",")
        if unit == PvPiUnits.mA:
            return int(value) / 1000
        else:
            raise ValueError("Failed to read battery current")

    def get_pv_voltage(self) -> float:
        """Read PV (solar) voltage (V)"""
        resp = self._interface.write(b"GET_PV_V").decode()
        unit, value = resp.split(",")
        if unit == PvPiUnits.mV:
            return int(value) / 1000
        else:
            raise ValueError("Failed to read PV (solar) voltage")

    def get_pv_current(self):
        """Read PV (solar) current (A)"""
        resp = self._interface.write(b"GET_PV_C").decode()
        unit, value = resp.split(",")
        if unit == PvPiUnits.mA:
            return int(value) / 1000
        else:
            raise ValueError("Failed to read PV (solar) current")

    def get_board_temp(self) -> int:
        """Get the PVPI Board temperature (Degrees Celsius)"""
        resp = self._interface.write(b"GET_TEMP").decode()
        type_, value = resp.split(",")
        if type_ == "TEMP":
            return int(value)  # TODO for real? int? also degs?
        else:
            raise ValueError("Failed to read board temperature")

    # ---------------------- Time Sync Commands ---------------------- #
    def set_mcu_time(self, dt: datetime | None = None):
        """Set STM32 RTC"""
        dt = dt or datetime.now()
        cmd = f"SET_TIME,{dt.year % 100},{dt.month},{dt.day},{dt.hour},{dt.minute},{dt.second}"
        resp = self._interface.write(cmd.encode())
        logging.info(f"Set MCU to System time: {dt.strftime('%y-%m-%d %H:%M:%S')}")
        return resp  # TODO what is resp and lets just return the obj rather than log

    def get_mcu_time(self) -> datetime:
        """Read STM32 RTC"""
        resp = self._interface.write(b"GET_TIME").decode()
        type_, *values = resp.split(",")
        if type_ == "GET_TIME":
            try:
                year, month, day, hour, minute, second = map(int, values)
                dt = datetime(2000 + year, month, day, hour, minute, second)
                return dt
            except Exception:
                _logger.error("Failed to parse STM32 RTC response %b", values)
                raise
        else:
            raise ValueError("Failed to read STM32 RTC")

    def set_alarm(self, pyt: time):
        """Set STM32 alarm using a datetime time object"""  # TODO update
        cmd = f"SET_ALARM,{pyt.hour},{pyt.minute},{pyt.second}".encode()
        resp = self._interface.write(cmd).decode().replace(" ", "")
        type_, value = resp.split(",")
        # TODO explain what's recvd

        cmd_state = resp.split(",")[1] if "," in resp else "FAIL"
        if cmd_state == "OK":
            logging.info(f"PV PI Alarm Set at: {pyt}")
            return True
        else:
            logging.warning("Failed to set alarm!")
            return False

    # ---------------------- Power Commands ---------------------- #
    def power_off(self, delay_s=30):
        """Schedule power-off after delay (seconds)"""
        cmd = f"POWER_OFF,{delay_s}".encode()
        resp = self._interface.write(cmd).decode()
        type_, value = resp.split(",")
        # TODO explain what's recvd

        cmd_state = resp.split(",")[1] if "," in resp else "FAIL"

        if cmd_state == "OK":
            logging.info(f"System Power OFF in {delay_s} seconds")
            return True
        else:
            logging.warning("Failed to Set Power off!")
            return False

    def set_watchdog(self, watchdog_period):  # TODO unit
        """Set the power watchdog"""
        cmd = f"WATCHDOG_ON,{watchdog_period}".encode()
        resp = self._interface.write(cmd).decode()
        type_, value = resp.split(",")
        # TODO explain what's recvd

        cmd_state = resp.split(",")[1] if "," in resp else "FAIL"
        if cmd_state == "OK":
            logging.info(f"PV PI Watchdog set with period: {watchdog_period}")
            return True
        else:
            logging.warning(f"Failed to set Watchdog! Response: {resp}")
            return False

    def stop_watchdog(self):
        """Stop the Power watchdog"""
        resp = self._interface.write(b"WATCHDOG_OFF").decode()
        type_, value = resp.split(",")
        # TODO explain what's recvd

        cmd_state = resp.split(",")[1] if "," in resp else "FAIL"
        if cmd_state == "OK":
            logging.info("PV PI Watchdog OFF")
            return True
        else:
            raise ValueError("Faield to stop watchdog")

    def set_wakeup_voltage(self, voltage: float):
        """Set the voltage at which the PV PI will wake the system"""
        if voltage < 11.5 or voltage > 14.4:
            raise ValueError(f"Voltage value {voltage} is invalid! Must be >11.5 and <14.4")

        millivolts = voltage * 1000
        cmd = f"SET_WAKEUP_MILIVOLT,{millivolts}".encode()
        resp = self._interface.write(cmd).decode()
        type_, value = resp.split(",")
        # TODO explain what's recvd

        cmd_state = resp.split(",")[1] if "," in resp else "FAIL"
        if cmd_state == "OK":
            logging.info(f"PV PI Wakeup Voltage set to: {voltage}")
            return True
        else:
            logging.warning(f"Failed to set Wakeup Voltage {voltage}, Response: {resp}")
            return False

    def set_max_charge_current(self, current: float):
        """Set the maxumin battery charge current for the the PV PI"""
        if current < 0.4 or current > 10:
            raise ValueError(f"Current value {current} is invalid! Must be >0.4 and <10")

        milliamps = current * 1000
        cmd = f"SET_CHARGE_MILIAMPS,{milliamps}".encode()
        resp = self._interface.write(cmd).decode()
        type_, value = resp.split(",")
        # TODO explain what's recvd

        cmd_state = resp.split(",")[1] if "," in resp else "FAIL"
        if cmd_state == "OK":
            logging.info(f"PV PI Battery Charge Current set to: {current}")
            return True
        else:
            logging.warning(f"Failed to set Battery Charge Current {current}, Response: {resp}")
            return False

    # ---------------------- Fault and Status Commands ---------------------- #
    def get_charge_state_code(self):
        """Get PV PI charge state code"""
        resp = self._interface.write(b"GET_CHARGE_STATE").decode()
        type_, value = resp.split(",")
        # TODO explain what's recvd

        cmd_state = resp.split(",")[0] if "," in resp else "FAIL"
        if cmd_state == "CHARGE_STATE":
            charge_state_code = int(resp.split(",")[1])
            return charge_state_code
        else:
            logging.warning("Failed to get charge state!")
            return None

    def get_charge_state(self):  # TODO
        """Get PV PI charge state string"""
        charge_state_code = self.get_charge_state_code()
        if charge_state_code is not None:
            return self.charge_states[charge_state_code]
        else:
            return "NA"

    def get_fault_code(self):
        """Get PV PI fault code"""
        resp = self._interface.write(b"GET_FAULT_CODE").decode()
        type_, value = resp.split(",")
        # TODO explain what's recvd

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
        if fault_code is not None:  # FIXME
            fault_states_list = [PvPiFaultStates[bit] for bit in range(8) if fault_code & (1 << bit)]
            return fault_states_list
        else:
            return []

    # ---------------------- Set Behaviour Commands ---------------------- #
    def set_mppt_state(self, state: str):
        """Set the mppt"""
        state = state.upper()
        if not (state == "ON" or state == "OFF"):
            logging.warning(f"INVAILID STATE {state}")
            return "ERROR"

        cmd = f"SET_MPPT_STATE,{state}".encode()
        resp = self._interface.write(cmd).decode()
        type_, value = resp.split(",")
        # TODO explain what's recvd

        cmd_state = resp.split(",")[1] if "," in resp else "FAIL"
        if cmd_state == "OK":
            logging.info(f"PV PI MPPT set: {state}")
            return state
        else:
            logging.warning(f"Failed to set PV PI MPPT! Response: {resp}")
            return "ERROR"

    def set_ts_state(self, state: str):
        """Enable/Disable the ts"""
        state = state.upper()
        if not (state == "ON" or state == "OFF"):
            logging.warning(f"INVAILID STATE {state}")
            return "ERROR"

        cmd = f"SET_TS_STATE,{state}".encode()
        resp = self._interface.write(cmd).decode()
        type_, value = resp.split(",")
        # TODO explain what's recvd

        cmd_state = resp.split(",")[1] if "," in resp else "FAIL"
        if cmd_state == "OK":
            logging.info(f"PV PI TS set: {state}")
            return state
        else:
            logging.warning(f"Failed to set PV PI TS! Response: {resp}")
            return "ERROR"

    def set_charge_state(self, state: str):
        """Enable/Disable the PV PI charging"""
        state = state.upper()
        if not (state == "ON" or state == "OFF"):
            logging.warning(f"INVAILID STATE {state}")
            return "ERROR"

        cmd = f"SET_CHARGE_STATE,{state}".encode()
        resp = self._interface.write(cmd).decode()
        type_, value = resp.split(",")
        # TODO explain what's recvd

        cmd_state = resp.split(",")[1] if "," in resp else "FAIL"
        if cmd_state == "OK":
            logging.info(f"PV PI Charging set: {state}")
            return state
        else:
            logging.warning(f"Failed to set PV PI Charging! Response: {resp}")
            return "ERROR"
