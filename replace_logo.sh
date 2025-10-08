#!/bin/bash
# Logo Replacement Script for Haio Smart App

echo "=== Haio Logo Replacement ==="
echo ""

# Check if new logo file is provided
if [ -z "$1" ]; then
    echo "Usage: ./replace_logo.sh <path-to-new-logo.png>"
    echo ""
    echo "Example:"
    echo "  ./replace_logo.sh ~/Downloads/new-haio-logo.png"
    echo ""
    exit 1
fi

NEW_LOGO="$1"
CURRENT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_LOGO="$CURRENT_DIR/haio-logo.png"

# Check if new logo exists
if [ ! -f "$NEW_LOGO" ]; then
    echo "❌ Error: File not found: $NEW_LOGO"
    exit 1
fi

# Backup old logo if it exists
if [ -f "$TARGET_LOGO" ]; then
    BACKUP="$TARGET_LOGO.backup.$(date +%Y%m%d_%H%M%S)"
    echo "📦 Backing up old logo to: $BACKUP"
    cp "$TARGET_LOGO" "$BACKUP"
fi

# Copy new logo
echo "🎨 Copying new logo..."
cp "$NEW_LOGO" "$TARGET_LOGO"

if [ $? -eq 0 ]; then
    echo "✅ Logo replaced successfully!"
    echo ""
    echo "New logo location: $TARGET_LOGO"
    echo ""
    echo "Next steps:"
    echo "1. Run the app to see the new logo: python main_new.py"
    echo "2. If the logo doesn't look right, restore backup: mv $BACKUP $TARGET_LOGO"
else
    echo "❌ Error: Failed to copy logo"
    exit 1
fi
