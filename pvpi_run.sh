#!/bin/bash
cd /home/pi/Documents/PVPI_Manager
source venv/bin/activate
python system_manager.py --shutdown_time 20:30 --wakeup_time 07:00 --schedule_time --enable_watchdog  --port "/dev/ttyAMA0" 2>&1
