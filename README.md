# PVPI_Manager
Automatic device manager for the PVPI <br>
TODO:<br>
Create automated setup method<br>
Create manual UART communication examples<br>


## Install pip requirements including system-wide packages
```commandline
python -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

## Activate scripts
```commandline
chmod +x pvpi_run.sh
chmod +x uart_server.sh
chmod +x set_pvpi_time.sh
```
## Creating System services
### Creating a service for PV PI System Manager
```commandline
sudo cp pvpi_manager.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pvpi_manager.service
sudo systemctl start pvpi_manager.service
```

### Creating a service for UART server
This is what is used to communicate to the PV PI.<br>
It creates a mini server that will relay commands over a websocket to the PV PI over UART.<br>
This way multiple different processes can send and receive commands to/from the PV PI!
```commandline
sudo cp uart_server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable uart_server.service
sudo systemctl start uart_server.service
```

### Controlling System services
 You can also use the "status", "stop" and "restart" commands!
```commandline
sudo systemctl status pvpi_manager.service
sudo systemctl stop pvpi_manager.service
sudo systemctl restart pvpi_manager.service
```
It's a good idea to stop the service running if you are still setting up the Pi!

### Viewing System service outputs
To view the live output from the PV PI Manager
```commandline
journalctl -u pvpi_manager.service -f
```

## Manually Set the PV PI STM32 RTC time to the SBC System time
You'll only need to do this once if you have a RTC backup battery
```commandline
./set_pvpi_time.sh
```

