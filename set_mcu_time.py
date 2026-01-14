from pvpi_client import PvPiNode

# ---------------------- CLI + Main ---------------------- #
def main():
    pvpi = PvPiNode()
    print("Checking connection...")
    print(f"Alive: {pvpi.get_alive()}")
    pvpi.set_mcu_time()
    print(f"Current MCU time: {pvpi.get_mcu_time()}")

if __name__ == "__main__":
    main()
