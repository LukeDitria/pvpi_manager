#!/bin/bash
cd /home/pi/Documents/PVPI_Manager
source venv/bin/activate
python uart_zmq_service.py 2>&1