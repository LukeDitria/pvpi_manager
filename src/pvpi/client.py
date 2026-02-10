import logging
from datetime import datetime, time
from enum import IntEnum, StrEnum
from typing import Literal

from pvpi.transports import BaseTransportInterface, SerialInterface, ZmqSerialProxyInterface

_logger = logging.getLogger(__name__)


class PvPiUnits(StrEnum):
    mV = "MILLIVOLTS"
    mA = "MILLIAMPS"


class PvPiChargeState(IntEnum):
    NotCharging = 0
    TrickleCharge = 1
    PreCharge = 2
    FastCharge = 3
    TaperCharge = 4
    NA = 5
    TopOffTimerCharge = 6
    ChargeTerminationDone = 7


PvPiChargeStateDescriptions = {
    PvPiChargeState.NotCharging: "Not charging",
    PvPiChargeState.TrickleCharge: "Trickle Charge (VBAT < VBAT_SHORT)",
    PvPiChargeState.PreCharge: "Pre-Charge (VBAT < VBAT_LOWV)",
    PvPiChargeState.FastCharge: "Fast Charge (CC mode)",
    PvPiChargeState.TaperCharge: "Taper Charge (CV mode)",
    PvPiChargeState.NA: "NA",
    PvPiChargeState.TopOffTimerCharge: "Top-off Timer Charge",
    PvPiChargeState.ChargeTerminationDone: "Charge Termination Done",
}


class PvPiFaultState(IntEnum):
    NA = 0
    DrvSupPinVoltage = 1
    ChargeSafetyTimer = 2
    ThermalShutdown = 3
    BatteryOverVoltage = 4
    BatteryOverCurrent = 5
    InputOverVoltage = 6
    InputUnderVoltage = 7


PvPiFaultStateDescriptions = {
    PvPiFaultState.NA: "NA",
    PvPiFaultState.DrvSupPinVoltage: "DRV_SUP pin voltage",
    PvPiFaultState.ChargeSafetyTimer: "Charge safety timer",
    PvPiFaultState.ThermalShutdown: "Thermal shutdown",
    PvPiFaultState.BatteryOverVoltage: "Battery over-voltage",
    PvPiFaultState.BatteryOverCurrent: "Battery over-current",
    PvPiFaultState.InputOverVoltage: "Input over-voltage",
    PvPiFaultState.InputUnderVoltage: "Input under-voltage",
}


def _get_interface():
    try:
        interface = ZmqSerialProxyInterface()
        _logger.info("Defaulted to ZmqSerialProxyInterface")
        return interface
    except Exception:
        _logger.info("Defaulted to SerialInterface")
        pass
    return SerialInterface()


class PvPiClient:
    def __init__(self, interface: BaseTransportInterface | None = None):
        self._interface = interface or _get_interface()

    def get_alive(self) -> bool:
        """Return True if PV PI is responsive"""
        return self._interface.write(message=b"GET_ALIVE") == "ALIVE"

    def get_battery_voltage(self) -> float:
        """Read battery voltage (V)"""
        resp = self._interface.write(b"GET_BAT_V")
        unit, value = resp.split(",")
        if unit == PvPiUnits.mV:
            return int(value) / 1000
        else:
            raise ValueError("Failed to read battery voltage")

    def get_battery_current(self) -> float:
        """Read battery current (A)"""
        resp = self._interface.write(b"GET_BAT_C")
        unit, value = resp.split(",")
        if unit == PvPiUnits.mA:
            return int(value) / 1000
        else:
            raise ValueError("Failed to read battery current")

    def get_pv_voltage(self) -> float:
        """Read PV (solar) voltage (V)"""
        resp = self._interface.write(b"GET_PV_V")
        unit, value = resp.split(",")
        if unit == PvPiUnits.mV:
            return int(value) / 1000
        else:
            raise ValueError("Failed to read PV (solar) voltage")

    def get_pv_current(self):
        """Read PV (solar) current (A)"""
        resp = self._interface.write(b"GET_PV_C")
        unit, value = resp.split(",")
        if unit == PvPiUnits.mA:
            return int(value) / 1000
        else:
            raise ValueError("Failed to read PV (solar) current")

    def get_board_temp(self) -> int:
        """Get the PVPI Board temperature (Degrees Celsius)"""
        resp = self._interface.write(b"GET_TEMP")
        type_, value = resp.split(",")
        if type_ == "TEMP":
            return int(value)
        else:
            raise ValueError("Failed to read board temperature")

    # ---------------------- Time Sync Commands ---------------------- #
    def set_mcu_time(self, dt: datetime | None = None):
        """Returns success bool for setting STM32 RTC"""
        dt = dt or datetime.now()
        cmd = f"SET_TIME,{dt.year % 100},{dt.month},{dt.day},{dt.hour},{dt.minute},{dt.second}"
        resp = self._interface.write(cmd.encode())
        _, success = resp.split(",")
        if success != "OK":
            raise ValueError("Failed to set MCU time")

    def get_mcu_time(self) -> datetime:
        """Read STM32 RTC"""
        resp = self._interface.write(b"GET_TIME")
        type_, *values = resp.split(",")
        if type_ != "GET_TIME":
            raise ValueError("Failed to read STM32 RTC")
        try:
            year, month, day, hour, minute, second = map(int, values)
            dt = datetime(2000 + year, month, day, hour, minute, second)
            return dt
        except Exception:
            _logger.error("Failed to parse STM32 RTC response %s", values)
            raise

    def set_alarm(self, pyt: time):
        """Set Pv PI STM32 alarm using a datetime time object"""
        cmd = f"SET_ALARM,{pyt.hour},{pyt.minute},{pyt.second}".encode()
        resp = self._interface.write(cmd).replace(" ", "")
        _, success = resp.split(",")
        if success != "OK":
            raise ValueError("Failed to set alarm")

    # ---------------------- Power Commands ---------------------- #
    def power_off(self, delay_s: int = 30):
        """Schedule power-off after delay (seconds)"""
        if delay_s < 1 or delay_s > 60:
            raise ValueError("Power off delay must be between 1-60 secs")
        cmd = f"POWER_OFF,{delay_s}".encode()
        resp = self._interface.write(cmd)
        _, success = resp.split(",")
        if success != "OK":
            raise ValueError("Failed to power off")

    def set_watchdog(self, watchdog_period_min: int):
        """Set the power watchdog"""
        if watchdog_period_min < 1 or watchdog_period_min > 60:
            raise ValueError("Power watchdog period must be 1-60 mins")
        cmd = f"WATCHDOG_ON,{watchdog_period_min}".encode()
        resp = self._interface.write(cmd)
        _, success = resp.split(",")
        if success != "OK":
            raise ValueError("Failed to set power watchdog")

    def stop_watchdog(self):
        """Stop the Power watchdog"""
        resp = self._interface.write(b"WATCHDOG_OFF")
        _, success = resp.split(",")
        if success != "OK":
            raise ValueError("Failed to stop power watchdog")

    def set_wakeup_voltage(self, voltage: float):
        """Set the voltage at which the PV PI will wake the system"""
        if voltage < 11.5 or voltage > 14.4:
            raise ValueError(f"Voltage value {voltage} is invalid! Must be >11.5 and <14.4")
        millivolts = voltage * 1000
        cmd = f"SET_WAKEUP_MILIVOLT,{millivolts}".encode()
        resp = self._interface.write(cmd)
        _, success = resp.split(",")
        if success != "OK":
            raise ValueError("Failed to set wakeup voltage")

    def set_max_charge_current(self, current: float):
        """Set the maximum battery charge current for the PV PI"""
        if current < 0.4 or current > 10:
            raise ValueError(f"Current value {current} is invalid! Must be >0.4 and <10")
        milliamps = current * 1000
        cmd = f"SET_CHARGE_MILIAMPS,{milliamps}".encode()
        resp = self._interface.write(cmd)
        _, success = resp.split(",")
        if success != "OK":
            raise ValueError("Failed to set max charge current")

    # ---------------------- Fault and Status Commands ---------------------- #
    def get_charge_state_code(self) -> PvPiChargeState:
        """Get PV PI charge state"""
        resp = self._interface.write(b"GET_CHARGE_STATE")
        type_, value = resp.split(",")
        if type_ != "CHARGE_STATE":
            raise ValueError("Failed to read Pv Pi charge state")
        return PvPiChargeState(int(value))

    def get_charge_state(self) -> str:
        """Get PV PI charge state description"""
        charge_state_code = self.get_charge_state_code()
        return PvPiChargeStateDescriptions[charge_state_code]

    def get_fault_code(self) -> PvPiFaultState:
        """Get PV PI fault code"""
        resp = self._interface.write(b"GET_FAULT_CODE")
        type_, value = resp.split(",")
        if type_ != "FAULT_CODE":
            raise ValueError("Failed to read Pv Pi fault state")
        return PvPiFaultState(int(value))

    def get_fault_states(self) -> str:
        """Get PV PI fault states description"""
        fault_code = self.get_fault_code()
        return PvPiFaultStateDescriptions[fault_code]

    # ---------------------- Set Behaviour Commands ---------------------- #
    def set_mppt_state(self, state: Literal["ON", "OFF"]):
        """Enable/Disable the Maximum Power Point Tracking"""
        state = state.upper()
        if state not in ("ON", "OFF"):
            raise ValueError("State can only be set to 'ON' or 'OFF'")
        cmd = f"SET_MPPT_STATE,{state}".encode()
        resp = self._interface.write(cmd)
        _, success = resp.split(",")
        if success != "OK":
            raise ValueError("Failed to set MPPT")

    def set_ts_state(self, state: Literal["ON", "OFF"]):
        """Enable/Disable the BQ25756 Battery Temperature monitoring"""
        state = state.upper()
        if state not in ("ON", "OFF"):
            raise ValueError("State can only be set to 'ON' or 'OFF'")
        cmd = f"SET_TS_STATE,{state}".encode()
        resp = self._interface.write(cmd)
        _, success = resp.split(",")
        if success != "OK":
            raise ValueError("Failed to set TS")

    def set_charge_state(self, state: Literal["ON", "OFF"]):
        """Enable/Disable the PV PI charging"""
        state = state.upper()
        if state not in ("ON", "OFF"):
            raise ValueError("State can only be set to 'ON' or 'OFF'")
        cmd = f"SET_TS_STATE,{state}".encode()
        resp = self._interface.write(cmd)
        _, success = resp.split(",")
        if success != "OK":
            raise ValueError("Failed to set charging state")
