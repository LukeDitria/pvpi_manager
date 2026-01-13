# PVPI_Manager
Automatic device manager for the PVPI <br>
TODO:<br>
Create manual UART communication examples<br>


# Setup and install
To setup an install the PV PI on your Raspberry Pi or other SBC login to your device and using the terminal run the following commands!

## Enable UART
Before setting up the PV PI you will need to enable the UART port on your device.<br>
For the Raspberry Pi and other SBC using the 40pin header the PV PI will use the UART port on pins GPIO 14/15.<br>
For the Raspberry Pi you can do this via raspi-config.<br>
You will then need to set the uart_port parameter of the config.json file to the UART port location.<br>
For the Raspberry Pi 5 etc this is usually /dev/ttyAMA0 <br> 
For the Raspberry Pi Zero this is usually /dev/ttyS0 <br> 

## Activate setup script
```commandline
chmod +x setup.sh
```

## Run setup/install
```commandline
./setup.sh
```

# System services
The PV PI manager creates 2 system services that will startup and run automatically upon every boot up!<br>

#### uart_server.service
This service is what is used to communicate to the PV PI.
It creates a mini server that will relay commands from a websocket to the PV PI over UART.
This way multiple different processes can send and receive commands to/from the PV PI! 

#### pvpi_manager.service
This is the main PV PI manager service. It loads the values in the config.json and performs system management as per the specified configurations. 

## Controlling System services
Both of these system services are set to start runnig straight away during the setup step.<br>
You can control either service with the following commands: "status", "stop", "start" and "restart".<br>
For example:
```commandline
sudo systemctl status pvpi_manager.service
sudo systemctl start pvpi_manager.service
sudo systemctl stop pvpi_manager.service
sudo systemctl restart pvpi_manager.service
```
It's a good idea to stop the service running if you are still setting up the Pi!

## Viewing System service outputs
To view the output from either service use journalctl.

To view the <b>live</b> (live updates) output from either service use -f.
```commandline
journalctl -u pvpi_manager.service -f
```

To view a history of the output from the most recent logs (static output) for either service use -e
```commandline
journalctl -u pvpi_manager.service -e
```


## Manually Set the PV PI STM32 RTC time to the SBC System time
To sync the time on the PV PI RTC we can send a "set time" command using the PV PI Manager.<br>
You'll only need to do this once if you have a RTC backup battery connected to the PV PI.<br>
Make sure that the uart_server.service is running first!
```commandline
./set_pvpi_time.sh
```
If you don't have a RTC backup battery then the RTC will loose time whenever the main battery power is diconnected.<br>
If you are relying on the the Raspberry Pi's (or other SBC) system time, then you should set time_pi2mcu to true in the config.json.

