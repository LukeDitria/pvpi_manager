import asyncio
import logging
from datetime import datetime

import click

from pvpi.client import PvPiClient
from pvpi.config import PvPiConfig
from pvpi.logging_ import init_logging
from pvpi.services import system_manager
from pvpi.services.zmq_serial_proxy import ZmqSerialProxy
from pvpi.systemd.install import install_systemd
from pvpi.transports import SerialInterface

logger = logging.getLogger("pvpi")

# TODO
#  - check config works with install dir
#  - check test cli
#  - check systemd install


@click.group()
@click.option("--verbose", is_flag=True, help="Enable debug logging.")
def cli(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    init_logging(logger=logger, level=level)


@cli.command(short_help="Set Pv Pi MCU clock to match current device clock")
def set_mcu_clock():
    pvpi = PvPiClient()
    pvpi.get_alive()
    pvpi.set_mcu_time()
    logger.info("Current MCU time: %s", pvpi.get_mcu_time())


@cli.command(short_help="Run Pv Pi function test with default parameters")
def connection_test():
    client = PvPiClient()
    logger.info("Running PV PI function test!")
    logger.info("Checking connection...")

    is_alive = client.get_alive()
    client.set_mcu_time()
    mcu_time = client.get_mcu_time()
    logger.info("Alive: %s", is_alive)
    logger.info("Current MCU time: %s", mcu_time)
    logger.info("System time: %s", datetime.now().strftime("%y-%m-%d %H:%M:%S"))

    logger.info("Set PV PI time from system time: %s", client.set_mcu_time())
    logger.info("New MCU time: %s", client.get_mcu_time())

    logger.info("PV PI Setting States...")
    client.set_mppt_state("ON")
    logger.info("PV PI Set MPPT State: ON")
    client.set_ts_state("OFF")
    logger.info("PV PI Set TS State: OFF")
    client.set_charge_state("ON")
    logger.info("PV PI Set Charge State: ON")
    client.set_max_charge_current(10)
    logger.info("PV PI Set MAX Charge Current: 10A")
    client.set_wakeup_voltage(13)
    logger.info("PV PI Set Wakeup Voltage: 13V")

    logger.info("PV PI Charge state code: %s", client.get_charge_state_code())
    logger.info("PV PI Charge state: %s", client.get_charge_state())
    logger.info("PV PI Fault code: %s", client.get_fault_code())
    logger.info("PV PI Fault state: %s", client.get_fault_states())

    logger.info("PV PI Battery and PV input...")
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
def uart_proxy(config: str | None = None):
    _config = PvPiConfig.from_file(path=config)
    serial_interface = SerialInterface(port=_config.uart_port)
    proxy_server = ZmqSerialProxy(serial_interface=serial_interface)
    asyncio.run(proxy_server.run())


@cli.command()
@click.option("--config", type=click.Path(exists=True, file_okay=True, dir_okay=False))
def manager(config: str | None = None):
    _config = PvPiConfig.from_file(path=config)
    system_manager.run(config=config)


@cli.command(short_help="Install Pv Pi logger & UART proxy as systemd services")
@click.option("--user", is_flag=True, help="Install systemd services as current user rather than root")
@click.option("--config", type=click.Path(exists=True, file_okay=True, dir_okay=False))
def install(user: bool = False, config: str | None = None):
    _config = PvPiConfig.from_file(path=config)

    install_systemd(user=user)  # TODO test


if __name__ == "__main__":
    cli()
