This is a PyQt6-based desktop application for mounting S3 buckets as local drives on Windows and Linux.

## Project Structure
- `main.py` - Main application with modern PyQt6 GUI
- `requirements.txt` - Python dependencies
- `s3_mounter.spec` - PyInstaller configuration
- `build.sh` / `build.bat` - Build scripts for packaging
- `README.md` - Documentation

## Key Features
- Modern UI with grouped controls and styling
- Cross-platform support (Windows/Linux)
- Connection testing before mounting
- Real-time logging and status updates
- Threaded mount operations
- Self-contained executable packaging

## Development
- Uses PyQt6 for the GUI framework
- boto3 for AWS S3 integration
- s3fs and fusepy for filesystem mounting
- PyInstaller for creating standalone executables

## Building
Run `./build.sh` (Linux) or `build.bat` (Windows) to create standalone executable with all dependencies included.
