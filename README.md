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

# Usage

```python
from pvpi import PvPiClient

client = PvPiClient()
print(client.get_alive())
```

Check out the [client.py](src/pvpi/client.py) for more details.

## Set Pv Pi STM32 RTC clock time
The Pv Pi's RTC can receive a "set clock" command using the SDK. You'll only need to do this once if you have a RTC backup battery connected to the Pv Pi. If you don't have a RTC backup battery then the RTC will loose time whenever the main battery power is disconnected.  

The following command will set the Pv Pi clock to match the system time of the machine calling the command (give or take a second or so).

```shell
uv run pvpi set-mcu-clock
```

## Install PV Pi Manager Service

Pv Pi manager comes with an `install` command to setup an automatic PV Pi Manager Service that will handle power management and scheduling. 

```shell
uv run pvpi install
```

The installation places two system services that will run automatically upon every boot. There is:
- The UART Proxy is a service that manages communications to the Pv PI for multiple applications attempting to do so at once. It holds onto the serial connection to the Pv Pi and proxies requests over network sockets.
- The Manager services is a simple looping script that communicates, via the UART proxy, to the Pv Pi and logs metrics.

This is an optional installation. Each service can be run directly via the CLI, and neither are required to run in order to use the Pv Pi SDK. The serve as examples on which to base your own work.

### More about systemd

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

## Update PV Pi Manager config
When you install the PV Pi Manager service a default config.json file will be created in the pvpi_manager directory. Subsequent restarts of the PV Pi Manager services will load configuration parameters from this config.json.

You can change the behaviour of the PV Pi Manager services by editing and saving this file and restarting the PV Pi Manager services.
```shell
uv run pvpi restart
```
