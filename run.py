#!/usr/bin/env python3
"""
Haio Smart Storage App Launcher
Runs the application with the correct module structure.
"""

import sys
import os

# Add the client directory to Python path if running from elsewhere
client_dir = os.path.dirname(os.path.abspath(__file__))
if client_dir not in sys.path:
    sys.path.insert(0, client_dir)

# Run the app as a module
if __name__ == "__main__":
    from src.main import main
    main()
