#!/bin/bash
echo "Installing Dependencies..."
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate

chmod +x pvpi_run.sh
chmod +x uart_server.sh
chmod +x set_pvpi_time.sh
chmod +x pvpi_test.sh

echo "Configuring systemd services..."
sudo sed -e "s|TARGET_USER|$USER|g" -e "s|TARGET_DIR|$PWD|g" pvpi_manager.service | sudo tee /etc/systemd/system/pvpi_manager.service > /dev/null
sudo sed -e "s|TARGET_USER|$USER|g" -e "s|TARGET_DIR|$PWD|g" uart_server.service | sudo tee /etc/systemd/system/uart_server.service > /dev/null

echo "Reloading systemd and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable pvpi_manager.service
sudo systemctl start pvpi_manager.service

sudo systemctl enable uart_server.service
sudo systemctl start uart_server.service

echo "Setup complete"