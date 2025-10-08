#!/bin/bash
# Setup script for Haio Drive Client on Linux

echo "Setting up Haio Drive Client for Linux..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check and install rclone
if ! command_exists rclone; then
    echo "Installing rclone..."
    curl https://rclone.org/install.sh | sudo bash
    if [ $? -eq 0 ]; then
        echo "✓ rclone installed successfully"
    else
        echo "✗ Failed to install rclone"
        exit 1
    fi
else
    echo "✓ rclone is already installed"
fi

# Check and install FUSE
if [ ! -f "/usr/bin/fusermount" ] && [ ! -f "/bin/fusermount" ]; then
    echo "Installing FUSE..."
    
    # Detect package manager
    if command_exists apt-get; then
        sudo apt-get update && sudo apt-get install -y fuse
    elif command_exists yum; then
        sudo yum install -y fuse
    elif command_exists dnf; then
        sudo dnf install -y fuse
    elif command_exists pacman; then
        sudo pacman -S fuse2
    else
        echo "✗ Unable to automatically install FUSE. Please install it manually."
        exit 1
    fi
    
    if [ $? -eq 0 ]; then
        echo "✓ FUSE installed successfully"
    else
        echo "✗ Failed to install FUSE"
        exit 1
    fi
else
    echo "✓ FUSE is already installed"
fi

# Set permissions for FUSE
if [ -f "/etc/fuse.conf" ]; then
    if ! grep -q "user_allow_other" /etc/fuse.conf; then
        echo "Configuring FUSE permissions..."
        echo "user_allow_other" | sudo tee -a /etc/fuse.conf
    fi
fi

echo "✓ Setup completed successfully!"
echo ""
echo "You can now run the Haio Drive Client:"
echo "  python3 main_new.py"
echo ""
echo "Or build a standalone executable:"
echo "  ./build.sh"
