from pvpi_client import PvPiNode
from datetime import datetime
import time

def main():
    pvpi = PvPiNode()
    print("Running PV PI function test!")
    print("Checking connection...")
    print(f"Alive: {pvpi.get_alive()}")
    pvpi.set_mcu_time()

    print("\n####PV PI TIME test!####")
    print(f"Current MCU time: {pvpi.get_mcu_time()}")
    print(f"System time: {datetime.now().strftime('%y-%m-%d %H:%M:%S')}")

    print(f"\n####PV PI Setting States TEST####")
    print(f"PV PI Set MPPT State: {pvpi.set_mppt_state("ON")}")
    print(f"PV PI Set TS State: {pvpi.set_ts_state("OFF")}")
    print(f"PV PI Set Charge State: {pvpi.set_charge_state("ON")}")

    print(f"\n####PV PI Set MAX Charge Current TEST####")
    print(f"PV PI Set MAX Charge Current: {pvpi.set_max_charge_current(10)}")

    print(f"\n####PV PI Set Wakeup Voltage TEST####")
    print(f"PV PI Set Wakeup Voltage: {pvpi.set_wakeup_voltage(13)}")

    print(f"\n####PV PI Charge and Fault Status TEST####")
    print(f"PV PI Charge State code: {pvpi.get_charge_state_code()}")
    print(f"PV PI Charge State: {pvpi.get_charge_state()}")

    print(f"PV PI fault code: {pvpi.get_fault_code()}")
    print(f"PV PI fault States: {pvpi.get_fault_states()}")

    print(f"\n####PV PI Battery and PV input TEST####")

    bat_v = pvpi.get_battery_voltage()
    bat_c = pvpi.get_battery_current()
    pv_v = pvpi.get_pv_voltage()
    pv_c = pvpi.get_pv_current()
    temperature = pvpi.get_board_temp()

    print(f"Battery: {bat_v} V, {bat_c} A")
    print(f"PV: {pv_v} V, {pv_c} A")
    print(f"PV PI Temp: {temperature}C")

if __name__ == "__main__":
    main()
