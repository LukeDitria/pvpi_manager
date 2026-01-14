from pvpi_client import PvPiManager
from datetime import datetime

def main():
    pvpi = PvPiManager()
    print("Checking connection...")
    print(f"Alive: {pvpi.get_alive()}")
    pvpi.set_mcu_time()
    print(f"Current MCU time: {pvpi.get_mcu_time()}")
    print(f"System time: {datetime.now().strftime('%y-%m-%d %H:%M:%S')}")

    print(f"PV PI Charge State code: {pvpi.get_charge_state_code()}")
    print(f"PV PI fault code: {pvpi.get_fault_code()}")

    print(f"PV PI Charge State: {pvpi.get_charge_state()}")
    print(f"PV PI fault States: {pvpi.get_fault_states()}")

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
