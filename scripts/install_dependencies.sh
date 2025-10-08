#!/bin/bash
# Automatic dependency installer for Haio Drive Client
# This script is bundled with the application and runs automatically when needed

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LOG_FILE="$SCRIPT_DIR/dependency_install.log"

# Function to log messages
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a "$LOG_FILE"
}

# Function to detect distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    elif [ -f /etc/redhat-release ]; then
        echo "rhel"
    else
        echo "unknown"
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Qt dependencies based on distribution
install_qt_dependencies() {
    local distro=$(detect_distro)
    log "Detected distribution: $distro"
    
    case "$distro" in
        ubuntu|debian)
            log "Installing Qt dependencies for Debian/Ubuntu..."
            apt update && apt install -y \
                libxcb-cursor0 \
                libxcb-icccm4 \
                libxcb-image0 \
                libxcb-keysyms1 \
                libxcb-render-util0 \
                libxcb-xinerama0 \
                libxcb-xfixes0 \
                libxkbcommon-x11-0 \
                qtwayland5
            ;;
        fedora|rhel|centos)
            log "Installing Qt dependencies for Fedora/RHEL/CentOS..."
            if command_exists dnf; then
                dnf install -y \
                    qt6-qtbase \
                    qt6-qtwayland \
                    libxcb \
                    xcb-util-cursor \
                    xcb-util-image \
                    xcb-util-keysyms \
                    xcb-util-renderutil \
                    xcb-util-wm \
                    libxkbcommon-x11
            elif command_exists yum; then
                yum install -y \
                    qt6-qtbase \
                    qt6-qtwayland \
                    libxcb \
                    xcb-util-cursor \
                    xcb-util-image \
                    xcb-util-keysyms \
                    xcb-util-renderutil \
                    xcb-util-wm \
                    libxkbcommon-x11
            fi
            ;;
        arch|manjaro)
            log "Installing Qt dependencies for Arch Linux..."
            pacman -S --noconfirm \
                qt6-base \
                qt6-wayland \
                libxcb \
                xcb-util-cursor \
                xcb-util-image \
                xcb-util-keysyms \
                xcb-util-renderutil \
                xcb-util-wm \
                libxkbcommon-x11
            ;;
        opensuse*|sles)
            log "Installing Qt dependencies for openSUSE/SLES..."
            zypper install -y \
                libQt6Core6 \
                libQt6Gui6 \
                libQt6Widgets6 \
                libxcb-cursor0 \
                libxcb-icccm4 \
                libxcb-image0 \
                libxcb-keysyms1 \
                libxcb-render-util0 \
                libxcb-xinerama0 \
                libxkbcommon-x11-0
            ;;
        *)
            log "Unknown distribution: $distro"
            log "Please install Qt dependencies manually."
            return 1
            ;;
    esac
}

# Function to install rclone if not present
install_rclone() {
    if ! command_exists rclone; then
        log "Installing rclone..."
        curl -sSL https://rclone.org/install.sh | bash
        if [ $? -eq 0 ]; then
            log "✓ rclone installed successfully"
        else
            log "✗ Failed to install rclone"
            return 1
        fi
    else
        log "✓ rclone is already installed"
    fi
}

# Function to install FUSE
install_fuse() {
    local distro=$(detect_distro)
    
    if [ ! -f "/usr/bin/fusermount" ] && [ ! -f "/bin/fusermount" ]; then
        log "Installing FUSE..."
        
        case "$distro" in
            ubuntu|debian)
                apt install -y fuse
                ;;
            fedora|rhel|centos)
                if command_exists dnf; then
                    dnf install -y fuse
                elif command_exists yum; then
                    yum install -y fuse
                fi
                ;;
            arch|manjaro)
                pacman -S --noconfirm fuse2
                ;;
            opensuse*|sles)
                zypper install -y fuse
                ;;
            *)
                log "Unable to install FUSE automatically on $distro"
                return 1
                ;;
        esac
        
        # Set FUSE permissions
        if [ -f "/etc/fuse.conf" ]; then
            if ! grep -q "user_allow_other" /etc/fuse.conf; then
                echo "user_allow_other" >> /etc/fuse.conf
                log "✓ FUSE permissions configured"
            fi
        fi
        
        log "✓ FUSE installed successfully"
    else
        log "✓ FUSE is already installed"
    fi
}

# Main installation function
main() {
    log "Starting Haio Drive Client dependency installation..."
    
    # Check if running as root (required for package installation)
    if [ "$EUID" -ne 0 ]; then
        log "Error: This script must be run with sudo privileges"
        echo "Please run: sudo $0"
        exit 1
    fi
    
    # Install dependencies
    log "Installing system dependencies..."
    
    # Install Qt dependencies
    if ! install_qt_dependencies; then
        log "Warning: Qt dependency installation failed"
    fi
    
    # Install rclone
    if ! install_rclone; then
        log "Error: rclone installation failed"
        exit 1
    fi
    
    # Install FUSE
    if ! install_fuse; then
        log "Warning: FUSE installation failed"
    fi
    
    log "✓ Dependency installation completed successfully!"
    log "You can now run the Haio Drive Client."
}

# Show usage if called with --help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Haio Drive Client Dependency Installer"
    echo ""
    echo "This script automatically installs required dependencies:"
    echo "  - Qt6/PyQt6 libraries (libxcb, qtwayland, etc.)"
    echo "  - rclone (cloud storage client)"
    echo "  - FUSE (filesystem in userspace)"
    echo ""
    echo "Usage:"
    echo "  sudo $0                 # Install all dependencies"
    echo "  $0 --help             # Show this help"
    echo ""
    echo "Supported distributions:"
    echo "  - Ubuntu/Debian (apt)"
    echo "  - Fedora/RHEL/CentOS (dnf/yum)"
    echo "  - Arch Linux (pacman)"
    echo "  - openSUSE/SLES (zypper)"
    exit 0
fi

# Run main installation
main "$@"