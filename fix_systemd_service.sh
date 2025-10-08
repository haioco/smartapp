#!/bin/bash
# Script to fix the systemd service rclone path

SERVICE_NAME="haio-haio331757338526-documents.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"

echo "Fixing systemd service: $SERVICE_NAME"

# Stop the service
sudo systemctl stop "$SERVICE_NAME" 2>/dev/null

# Update the ExecStart line to use system rclone
sudo sed -i 's|ExecStart=/tmp/[^/]*/rclone|ExecStart=/usr/bin/rclone|g' "$SERVICE_FILE"

# Also change Type from simple to notify if needed
sudo sed -i 's|Type=simple|Type=notify|g' "$SERVICE_FILE"

# Reload systemd
sudo systemctl daemon-reload

echo "Service file updated!"
echo ""
echo "Current ExecStart line:"
grep "ExecStart" "$SERVICE_FILE"
echo ""

# Ask if user wants to restart the service
read -p "Do you want to start the service now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl start "$SERVICE_NAME"
    echo "Service started. Status:"
    systemctl status "$SERVICE_NAME" --no-pager -l
fi
