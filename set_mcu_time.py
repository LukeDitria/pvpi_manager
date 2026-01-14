from pvpi_client import PvPiManager

# ---------------------- CLI + Main ---------------------- #
def main():
    pvpi = PvPiManager()
    print("Checking connection...")
    print(f"Alive: {pvpi.get_alive()}")
    pvpi.set_mcu_time()
    print(f"Current MCU time: {pvpi.get_mcu_time()}")

if __name__ == "__main__":
    main()
