# PVPI_Manager
Automatic device manager for the PVPI <br>
TODO:<br>
Create automated setup method
Create manual UART communication examples
Create config json method


## Install pip requirements including system-wide packages
(NOTHING TO INSTALL YET THOUGH...)
```commandline
python -m venv venv --system-site-packages
source venv/bin/activate
deactivate
```

## Activate scripts
```commandline
chmod +x pvpi_run.sh
chmod +x uart_server.sh
chmod +x set_pvpi_time.sh
```

## Creating a service for PV PI System Manager
```commandline
sudo cp pvpi_manager.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pvpi_manager.service
sudo systemctl start pvpi_manager.service
```

## Creating a service for UART server
```commandline
sudo cp uart_server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable uart_server.service
sudo systemctl start uart_server.service
```

 You can also use the "status", "stop" and "restart" commands!
```commandline
sudo systemctl status pvpi_manager.service
sudo systemctl stop pvpi_manager.service
sudo systemctl restart pvpi_manager.service
```
It's a good idea to stop the service running if you are still setting up the Pi!


To view the live output from the PV PI Manager
```commandline
journalctl -u pvpi_manager.service -f
```

## Set the PV PI STM32 RTC time

