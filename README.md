# pvpi_manager
The official Python SDK for the Pv Pi.

# Setup
## Requirements
PV PI Manager is designed to operate on Raspberry Pi compatible devices.  
The following setup was verified on a Raspberry Pi 5 with Raspberry Pi OS (64-bit) (Release: 2025-12-04).

### Python `uv`

Python packager manager [uv](https://docs.astral.sh/uv) is the preferred method for operating the PVPI.
```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Enabling UART
The PV PI communicates over the UART port. By default, the Raspberry Pi does not have this port enabled. Enable the UART port by:
1. `sudo raspi-config`
2. Select `3 Interface Options`
3. Select `I6 Serial Port`
4. Select "No" to "Would you like a login shell to be accessible over serial"
5. Select "Yes" to "Would you like the serial port hardware to be enabled."
6. Exit setup & reboot device.

For the Raspberry Pi and other SBC using the 40pin header the PV PI will use the UART port on pins GPIO 14/15. The PV PI manager auto-detects the board model and selects the correct default port:
- Raspberry Pi (standard models): `/dev/ttyAMA0`
- Raspberry Pi Zero variants: `/dev/ttyS0`

You can override the port by setting `uart_port` in the `config.json` file.

## Installation

Clone the repo:
```shell
git clone https://github.com/LukeDitria/pvpi_manager.git
cd pvpi_manager
uv sync
uv run pvpi
```

Or, add to you own Python project:
```shell
uv add git+https://github.com/LukeDitria/pvpi_manager.git
```

# Quick-start

```shell
cd pvpi_manager
uv run pvpi  # show usage help

uv run pvpi connection-test
```

## Install PV Pi Manager Service

Pv Pi manager comes with an `install` command to setup an automatic PV Pi Manager Service that will handle power management and scheduling. 

```shell
uv run pvpi install
```

The installation places two system services that will run automatically upon every boot. There is:
- The UART Proxy is a service that manages communications to the PV PI for multiple applications attempting to do so at once. It holds onto the serial connection to the PV Pi and proxies requests over network sockets.
- The Manager services is a simple looping script that communicates, via the UART proxy, to the PV Pi and logs metrics.
- The Dashboard is a simple Streamlit based dashboard to display live PV Pi statistics
as well as the historical data logs hosted on port 8501. Historical data log requires
log_pvpi_stats to be enabled

This is an optional installation. Each service can be run directly via the CLI, and neither are required to run in order to use the Pv Pi SDK. The serve as examples on which to base your own work.

# Other CLI commands

## Setting PV Pi STM32 RTC clock time
The PV Pi's RTC can receive a "set clock" command using the SDK. You'll only need to do this once if you have a RTC backup battery connected to the PV Pi. If you don't have a RTC backup battery then the RTC will loose time whenever the main battery power is disconnected.  

The following command will set the Pv Pi clock to match the system time of the machine calling the command (give or take a second or so).

```shell
uv run pvpi set-mcu-clock
```

## Restart PV Pi Systemd services
Restarts both the Pv Pi Manager & UART proxy systemd service.
```shell
uv run pvpi restart
```

## Get the PV Pi Battery/Solar Statistics
Prints out the current PV Pi temperature as well as Battery and Solar voltage and charge current.

```shell
uv run pvpi get-stats
```

## Get the BQ25756 charging State
Prints out the current state of the BQ25756 charge cycle.

```shell
uv run pvpi get-charge-state
```

## Get Pv Pi Fault States
Prints out the description of any current faults of the PV Pi/BQ25756.

```shell
uv run pvpi get-faults
```

## Set Pv Pi MPPT State
Enable/Disable Pv Pi MPPT.

With no flag MPPT will be disabled.
```shell
uv run pvpi set-mppt
```

With "enable" flag MPPT will be enabled.
```shell
uv run pvpi set-mppt --enable
```

## Set TS State 
Enable/Disable BQ25756 Battery Temperature monitoring.

With no flag Temperature monitoring will be disabled.
```shell
uv run pvpi set-ts
```

With "enable" flag Temperature monitoring will be enabled.
```shell
uv run pvpi set-ts --enable
```
## Set PV Pi Charging State
Enable/Disable PV Pi battery charging.

With no flag charging will be disabled.
```shell
uv run pvpi set-charging
```

With "enable" flag charging will be enabled.
```shell
uv run pvpi set-charging --enable
```



# Creating your own client node

```python
from pvpi import PvPiClient

client = PvPiClient()
print(client.get_alive())
```

Check out the [client.py](src/pvpi/client.py) for more details.

# More about systemd

(i) `systemd` is the standard system and service manager for modern Linux distributions. Once installed, you can check the `status`, `start`, `stop`, or `restart` these PV PI services using the `systemctl` command:
```shell
sudo systemctl status pvpi_manager.service
sudo systemctl status uart_server.service
```

While the status of services can be viewed with `systemctl` as shown above, the log output can be followed using `journalctl`.

To follow the **live** log output from either service:
```shell
journalctl -u pvpi_manager.service -f
journalctl -u uart_server.service -f
```

(i) `journalctl` is a Linux command-line tool for viewing and managing logs from `systemd`. Logs can be filtered by process and time. [Learn more](https://www.digitalocean.com/community/tutorials/how-to-use-journalctl-to-view-and-manipulate-systemd-logs).

# Updating the PV Pi Manager config
When you install the PV Pi Manager service a default config.json file will be created in the pvpi_manager directory. Subsequent restarts of the PV Pi Manager services will load configuration parameters from this config.json.

You can change the behaviour of the PV Pi Manager services by editing and saving this file and restarting the PV Pi Manager services.
```shell
uv run pvpi restart
```
