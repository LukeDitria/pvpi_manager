#!/bin/bash
echo "Installing systemd services..."
sudo sed -e "s|TARGET_USER|$USER|g" pvpi_manager.service | sudo tee /etc/systemd/system/pvpi_manager.service > /dev/null
sudo sed -e "s|TARGET_USER|$USER|g" uart_server.service | sudo tee /etc/systemd/system/uart_server.service > /dev/null

echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Starting PV Pi Manager service..."
sudo systemctl enable pvpi_manager.service
sudo systemctl start pvpi_manager.service

echo "Starting UART server service..."
sudo systemctl enable uart_server.service
sudo systemctl start uart_server.service

echo "Setup complete!"