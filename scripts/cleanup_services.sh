#!/bin/bash
# Haio Smart App - Manual Service Cleanup Script
# Use this if you cancelled the password prompt and need to remove services manually

echo "============================================================"
echo "Haio Smart App - Manual Auto-Mount Service Cleanup"
echo "============================================================"
echo ""
echo "This script will list and help you remove leftover auto-mount services."
echo ""

# Check if running on Linux
if [[ "$(uname)" != "Linux" ]]; then
    echo "❌ This script is for Linux only."
    echo "   Windows users: Use Task Scheduler to remove tasks manually."
    exit 1
fi

# Check for systemd services
echo "🔍 Scanning for Haio auto-mount services..."
echo ""

# Look for haio-* services in user systemd directory
USER_SERVICE_DIR="$HOME/.config/systemd/user"
SYSTEM_SERVICE_DIR="/etc/systemd/system"

found_services=()

# Check user services
if [ -d "$USER_SERVICE_DIR" ]; then
    while IFS= read -r service_file; do
        if [ -n "$service_file" ]; then
            service_name=$(basename "$service_file")
            found_services+=("user:$service_name")
        fi
    done < <(find "$USER_SERVICE_DIR" -name "haio-*.service" 2>/dev/null)
fi

# Check system services (requires sudo)
echo "Checking system services (may ask for password)..."
while IFS= read -r service_file; do
    if [ -n "$service_file" ]; then
        service_name=$(basename "$service_file")
        found_services+=("system:$service_name")
    fi
done < <(sudo find "$SYSTEM_SERVICE_DIR" -name "haio-*.service" 2>/dev/null)

if [ ${#found_services[@]} -eq 0 ]; then
    echo "✅ No Haio auto-mount services found!"
    echo ""
    echo "All clean! No manual cleanup needed."
    exit 0
fi

echo ""
echo "📋 Found ${#found_services[@]} Haio service(s):"
echo ""

for i in "${!found_services[@]}"; do
    service="${found_services[$i]}"
    type="${service%%:*}"
    name="${service#*:}"
    
    echo "  $((i+1)). [$type] $name"
    
    # Check if service is enabled
    if [ "$type" = "user" ]; then
        if systemctl --user is-enabled "$name" &>/dev/null; then
            echo "      Status: 🟢 Enabled"
        else
            echo "      Status: 🔴 Disabled"
        fi
    else
        if sudo systemctl is-enabled "$name" &>/dev/null; then
            echo "      Status: 🟢 Enabled"
        else
            echo "      Status: 🔴 Disabled"
        fi
    fi
done

echo ""
echo "============================================================"
echo "Would you like to remove these services?"
echo "============================================================"
echo ""
read -p "Remove all services? [y/N]: " -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled by user."
    echo ""
    echo "To remove services manually later, run:"
    echo "  User services:"
    echo "    systemctl --user disable <service-name>"
    echo "    systemctl --user stop <service-name>"
    echo "    rm ~/.config/systemd/user/<service-name>"
    echo "    systemctl --user daemon-reload"
    echo ""
    echo "  System services:"
    echo "    sudo systemctl disable <service-name>"
    echo "    sudo systemctl stop <service-name>"
    echo "    sudo rm /etc/systemd/system/<service-name>"
    echo "    sudo systemctl daemon-reload"
    exit 0
fi

echo "🧹 Removing services..."
echo ""

removed=0
failed=0

for service in "${found_services[@]}"; do
    type="${service%%:*}"
    name="${service#*:}"
    
    echo "Removing [$type] $name..."
    
    if [ "$type" = "user" ]; then
        # User service
        systemctl --user disable "$name" 2>/dev/null
        systemctl --user stop "$name" 2>/dev/null
        rm -f "$USER_SERVICE_DIR/$name"
        
        if [ ! -f "$USER_SERVICE_DIR/$name" ]; then
            echo "  ✅ Removed successfully"
            ((removed++))
        else
            echo "  ❌ Failed to remove"
            ((failed++))
        fi
    else
        # System service (needs sudo)
        sudo systemctl disable "$name" 2>/dev/null
        sudo systemctl stop "$name" 2>/dev/null
        sudo rm -f "$SYSTEM_SERVICE_DIR/$name"
        
        if [ ! -f "$SYSTEM_SERVICE_DIR/$name" ]; then
            echo "  ✅ Removed successfully"
            ((removed++))
        else
            echo "  ❌ Failed to remove"
            ((failed++))
        fi
    fi
done

# Reload systemd
echo ""
echo "Reloading systemd..."
systemctl --user daemon-reload 2>/dev/null
sudo systemctl daemon-reload 2>/dev/null

echo ""
echo "============================================================"
echo "Cleanup Summary"
echo "============================================================"
echo "  ✅ Removed: $removed service(s)"
echo "  ❌ Failed:  $failed service(s)"
echo ""

if [ $failed -eq 0 ]; then
    echo "🎉 All services removed successfully!"
else
    echo "⚠️  Some services could not be removed."
    echo "   Check permissions and try again."
fi

echo ""
