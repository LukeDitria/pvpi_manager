# PVPI_Manager
Automatic device manager for the PVPI


## Install pip requirements including system-wide packages
(NOTHING TO INSTALL YET THOUGH...)
```commandline
python -m venv venv --system-site-packages
source venv/bin/activate
deactivate
```

## Creating a service
```commandline
sudo cp pvpi_manager.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pvpi_manager.service
sudo systemctl start pvpi_manager.service
```
 You can also use the "status", "stop" and "restart" commands!
```commandline
sudo systemctl status pvpi_manager.service
sudo systemctl stop pvpi_manager.service
sudo systemctl restart pvpi_manager.service
```
It's a good idea to stop the service running if you are still setting up the Pi!
