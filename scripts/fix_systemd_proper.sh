#!/bin/bash
# Script to properly fix the systemd service

SERVICE_NAME="haio-haio331757338526-documents.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
CURRENT_USER=$(whoami)

echo "Fixing systemd service for user: $CURRENT_USER"
echo "Service file: $SERVICE_FILE"
echo ""

# Stop the service
echo "Stopping service..."
sudo systemctl stop "$SERVICE_NAME" 2>/dev/null
sudo systemctl disable "$SERVICE_NAME" 2>/dev/null

# Create new service file content
cat << EOF | sudo tee "$SERVICE_FILE" > /dev/null
[Unit]
Description=Haio Drive Mount - documents
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$CURRENT_USER
Environment=DrivePathDirectory="/home/$CURRENT_USER/haio-haio331757338526-documents"
Environment=CachePathDirectory="/home/$CURRENT_USER/.cache/rclone"
Environment=RcloneConfig="/home/$CURRENT_USER/.config/rclone/rclone.conf"
Environment=ConfigName="haio_haio331757338526"
Environment=ContainerName="documents"

ExecStartPre=/bin/mkdir -p "\${DrivePathDirectory}"
ExecStartPre=/bin/mkdir -p "\${CachePathDirectory}"
ExecStart=/usr/bin/rclone mount \\
        --allow-non-empty \\
        --dir-cache-time 10s \\
        --poll-interval 1m \\
        --vfs-cache-mode full \\
        --vfs-cache-max-age 24h \\
        --vfs-write-back 10s \\
        --vfs-read-wait 20ms \\
        --buffer-size 32M \\
        --attr-timeout 1m \\
        --cache-dir "\${CachePathDirectory}" \\
        --config "\${RcloneConfig}" \\
        --log-level INFO \\
        "\${ConfigName}:\${ContainerName}" "\${DrivePathDirectory}"
ExecStop=/bin/bash -c 'fusermount -u "\${DrivePathDirectory}" || umount -l "\${DrivePathDirectory}"'

# Restart configuration
Restart=on-failure
RestartSec=10
StartLimitIntervalSec=60
StartLimitBurst=3

# Resource limits
TimeoutStartSec=30
TimeoutStopSec=10

[Install]
WantedBy=default.target
EOF

echo "Service file updated!"
echo ""

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable and start service
echo "Enabling service..."
sudo systemctl enable "$SERVICE_NAME"

echo ""
read -p "Do you want to start the service now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting service..."
    sudo systemctl start "$SERVICE_NAME"
    sleep 2
    echo ""
    echo "Service status:"
    systemctl status "$SERVICE_NAME" --no-pager -l
    
    echo ""
    echo "Mount point check:"
    ls -la "/home/$CURRENT_USER/haio-haio331757338526-documents" | head -5
fi

echo ""
echo "Done! You can check logs with:"
echo "  sudo journalctl -u $SERVICE_NAME -f"
