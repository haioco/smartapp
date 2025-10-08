#!/bin/bash
# Quick fix for TempURL 401 error
# This resets your TempURL configuration

echo "🔧 TempURL 401 Quick Fix"
echo "======================================"
echo ""
echo "This will:"
echo "  1. Backup your current settings"
echo "  2. Remove the TempURL key"
echo "  3. Force the app to generate a new one"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

SETTINGS_FILE="$HOME/.config/Haio/SmartApp.conf"

if [ -f "$SETTINGS_FILE" ]; then
    echo ""
    echo "📋 Backing up settings..."
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    echo "   ✅ Backup created"
    
    echo ""
    echo "🗑️  Removing TempURL key from settings..."
    # Remove just the temp_url_key line
    sed -i '/temp_url_key/d' "$SETTINGS_FILE"
    echo "   ✅ Key removed"
    
    echo ""
    echo "======================================"
    echo "✅ Done!"
    echo "======================================"
    echo ""
    echo "Next steps:"
    echo "  1. Close the application (if running)"
    echo "  2. Start the application"
    echo "  3. Make sure you're logged in"
    echo "  4. Try sharing a file"
    echo ""
    echo "The app will generate a NEW key and set it"
    echo "on the server with your current login token."
    echo ""
    echo "If you still get 401:"
    echo "  → Logout and login again"
    echo "  → Then try sharing"
    
else
    echo ""
    echo "⚠️  Settings file not found: $SETTINGS_FILE"
    echo ""
    echo "This means:"
    echo "  - No configuration exists yet, OR"
    echo "  - You haven't logged in to the app yet"
    echo ""
    echo "Solution:"
    echo "  1. Start the application"
    echo "  2. Login with your credentials"
    echo "  3. Try sharing a file"
fi
