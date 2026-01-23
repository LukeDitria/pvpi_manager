# PVPI_Manager
Automatic device manager for the PVPI   
TODO:  
Create flag/notification from system manager so all pvpi nodes can know when system manager has started (after start-up delay). Could set flag on UART server with special command?  
Create location based sunrise to sunset schedule   
Create "periodic process" example template? A short bit of code/method that will run once and then shut down the device?  
Create manual UART communication examples  


# Setup and install
To setup an install the PV PI on your Raspberry Pi or other SBC login to your device and using the terminal run the following commands!

## Enable UART
Before setting up the PV PI you will need to enable the UART port on your device.  
For the Raspberry Pi and other SBC using the 40pin header the PV PI will use the UART port on pins GPIO 14/15.  
For the Raspberry Pi you can do this via raspi-config.  
By default the PV PI manager tries to use /dev/ttyAMA0, you can change this AFTER setup by modifying the generated config.json file.

## git clone this repo
Navigate to your home directory and git clone this repo
```commandline
cd --
git clone https://github.com/LukeDitria/pvpi_manager.git
```

## Enter the created directory and activate the setup script
```commandline
cd pvpi_manager
chmod +x setup.sh
```

## Run the setup/install script
```commandline
./setup.sh
```

# System services
The PV PI manager creates 2 system services that will startup and run automatically upon every boot up!  

#### uart_server.service
This service is what is used to communicate to the PV PI.
It creates a mini server that will relay commands from a websocket to the PV PI over UART.
This way multiple different processes can send and receive commands to/from the PV PI! 

#### pvpi_manager.service
This is the main PV PI manager service. It loads the values in the config.json and performs system management as per the specified configurations. 

## Controlling System services
Both of these system services are set to start running straight away during the setup step.  
You can control either service with the following commands: "status", "stop", "start" and "restart".  
For example:
```commandline
sudo systemctl status pvpi_manager.service
sudo systemctl stop pvpi_manager.service
sudo systemctl start pvpi_manager.service
sudo systemctl restart pvpi_manager.service
```
It's a good idea to stop the pvpi_manager.service from running if you are still setting up the Pi!

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

# Additional Setup

## Change UART
If you run the command
```commandline
journalctl -u uart_server.service -e
```
And see that the UART server cannot find the PV PI, then either UART has not been enabled or the wrong location is defined in the config.json.  
To update the port location, change the "uart_port" parameter of the config.json file to your UART port location.  
For the Raspberry Pi this is usually /dev/ttyAMA0    
For the Raspberry Pi ZERO this is usually /dev/ttyS0    
For other SBCs you'll need to consult the device documentation.  
  
Once you have changed the "uart_port" parameter, restart the uart server.

```commandline
sudo systemctl restart uart_server.service
```

## Manually Set the PV PI STM32 RTC time to the SBC System time
To sync the time on the PV PI RTC we can send a "set time" command using the PV PI Manager.  
You'll only need to do this once if you have a RTC backup battery connected to the PV PI.  
Make sure that the uart_server.service is running first!
```commandline
./set_pvpi_time.sh
```
This will return the current time from the PV PI which should match the system time (give or take a second or so).  
If you don't have a RTC backup battery then the RTC will loose time whenever the main battery power is disconnected.  
If you are relying on the the Raspberry Pi's (or other SBC) system time for time-keeping, then you should set time_pi2mcu to true in the config.json.

## Run PV PI Test
You can run the pvpi_test script (pvpi_test.py) by using the bash script:
```commandline
./pvpi_test.sh
```
pvpi_test.py is also a good example of how you can interact with the PV PI from another script via the PV PI node class in the pvpi_client directory.

## Install the PV PI Client in another repo
If you want to use the PV PI Node in another project you can pip install and link it to this repo, rather than simply copying it.
We do not yet have the PV PI wheel on PyPi but the PV PI Client is setup so you can easily pip install it.  
To do so, in your projects virtual environment run: 
```commandline
pip install -e /home/pi/pvpi_manager
```
Make sure that the full path to the pvpi_manager directory is the same as yours.
