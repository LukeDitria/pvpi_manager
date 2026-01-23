import asyncio
import logging
from datetime import datetime

import click
import serial

from pvpi.client import PvPiClient
from pvpi.services.zmq_serial_proxy import ZmqSerialProxy
from pvpi.transports import SerialInterface
from pvpi.utils import init_logging

logger = logging.getLogger("pvpi")

# TODO
#  - check config works with install dir
#  - check test cli
#  - check every client endpoint
#  - check systemd install


@click.group()
@click.option("--verbose", is_flag=True, help="Enable debug logging.")
def cli(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    init_logging(logger=logger, level=level)


@cli.command()
@click.option("--user", is_flag=True, help="Install systemd services as current user")
@click.option("--config", type=click.Path(exists=True, file_okay=True, dir_okay=False))
def install(user: bool = False, config: str = None):
    from pvpi.systemd.install import install_systemd

    # TODO grab config


    install_systemd(user=user)


@cli.command(short_help="Set Pv PI MCU clock to match device clock")
def set_mcu_time():
    pvpi = PvPiClient()
    logger.info(f"Alive: {pvpi.get_alive()}")
    pvpi.set_mcu_time()
    logger.info(f"Current MCU time: {pvpi.get_mcu_time()}")


@cli.command(name="test")
def pvpi_connection_test():
    client = PvPiClient()
    logger.info("Running PV PI function test!")
    logger.info("Checking connection...")

    is_alive = client.get_alive()
    client.set_mcu_time()
    mcu_time = client.get_mcu_time()
    logger.info("Alive: %s", is_alive)
    logger.info("Current MCU time: %s", mcu_time)
    logger.info("System time: %s", datetime.now().strftime("%y-%m-%d %H:%M:%S"))

    logger.info(f"Set PV PI time from system time: {client.set_mcu_time()}")
    logger.info(f"New MCU time: {client.get_mcu_time()}")

    logger.info("PV PI Setting States")
    logger.info(f"PV PI Set MPPT State: {client.set_mppt_state('ON')}")
    logger.info(f"PV PI Set TS State: {client.set_ts_state('OFF')}")
    logger.info(f"PV PI Set Charge State: {client.set_charge_state('ON')}")
    logger.info(f"PV PI Set MAX Charge Current: {client.set_max_charge_current(10)}")
    logger.info(f"PV PI Set Wakeup Voltage: {client.set_wakeup_voltage(13)}")

    logger.info(f"PV PI Charge State code: {client.get_charge_state_code()}")
    logger.info(f"PV PI Charge State: {client.get_charge_state()}")

    logger.info(f"PV PI Fault code: {client.get_fault_code()}")
    logger.info(f"PV PI Fault States: {client.get_fault_states()}")

    logger.info("PV PI Battery and PV input #")

    bat_v = client.get_battery_voltage()
    bat_c = client.get_battery_current()
    pv_v = client.get_pv_voltage()
    pv_c = client.get_pv_current()
    temperature = client.get_board_temp()
    logger.info("Battery: %s V, %s A", bat_v, bat_c)
    logger.info("PV: %s V, %s A", pv_v, pv_c)
    logger.info("PV PI Temp: %sC", temperature)


@cli.command()
@click.option("--config", type=click.Path(exists=True, file_okay=True, dir_okay=False))
def run_uart_proxy(config: str = None):
    # TODO grab config

    try:
        serial_interface = SerialInterface()
    except (serial.SerialException, Exception):
        logging.error("Failed to open serial port")
        raise

    try:
        proxy_server = ZmqSerialProxy(serial_interface=serial_interface)
    except Exception:
        logging.error("Failed to ...")  # TODO
        serial_interface.close()
        raise

    asyncio.run(proxy_server.run())

@cli.command()
@click.option("--config", type=click.Path(exists=True, file_okay=True, dir_okay=False))
def run_system_logger(config: str = None):
    # TODO grab config
    ...


if __name__ == "__main__":
    cli()
