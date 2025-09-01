# Haio Drive Client

A beautiful and modern desktop application for managing and mounting Haio cloud storage buckets using rclone.

## Features

### 🎨 Beautiful User Interface
- Modern, responsive design with smooth animations
- Frameless login dialog with gradient styling
- Intuitive bucket management interface
- Real-time mount status updates

### 🔐 Secure Authentication
- Token-based authentication with the Haio API
- Optional credential saving with "Remember me" option
- Automatic token management and refresh

### 💾 Bucket Management
- View all your storage buckets with detailed information
- See bucket size, object count, and usage statistics
- Mount/unmount buckets with a single click
- Real-time mount status monitoring

### 🗂️ Advanced Mounting
- Uses rclone for reliable, high-performance mounting
- Optimized mount options for best performance
- Automatic mount point creation
- Persistent mounting at boot time via systemd services

### ⚙️ System Integration
- Desktop application integration
- Systemd service creation for auto-mounting
- Cross-platform compatibility (Linux focus)

## Requirements

### System Requirements
- Linux operating system (Ubuntu, Debian, etc.)
- Python 3.8 or higher
- rclone installed (`sudo apt install rclone`)
- PyQt6 for the GUI

### Permissions
- Sudo access for creating systemd services (auto-mount feature)
- Read/write access to mount points (typically `/mnt/`)

## Installation

### Quick Start
1. Clone or download the repository
2. Navigate to the client directory
3. Run the build script:
   ```bash
   chmod +x build.sh
   ./build.sh
   ```
4. Launch the application:
   ```bash
   ./launch.sh
   ```

### Manual Installation
1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run from source:
   ```bash
   python3 main_new.py
   ```

## Usage

### First Time Setup
1. Launch the application
2. Enter your Haio username and password
3. Choose "Remember me" to save credentials
4. Click "Login" to authenticate

### Managing Buckets
1. After login, you'll see all your available buckets
2. Each bucket shows:
   - Bucket name and size
   - Number of objects
   - Current mount status
   - Mount point location

### Mounting Buckets
1. Click "Mount" on any bucket to mount it locally
2. The bucket will be available at `/mnt/haio-{username}-{bucket_name}`
3. Access your files through the file manager
4. Click "Unmount" when done

### Auto-Mount at Boot
1. Check "Auto-mount at boot" for any bucket
2. The application will create a systemd service
3. The bucket will automatically mount on system startup
4. Requires sudo privileges

### Configuration

#### Rclone Configuration
The application automatically creates rclone configuration at:
```
~/.config/rclone/rclone.conf
```

#### Application Settings
User settings and tokens are stored at:
```
~/.config/haio-client/
```

## API Integration

The client integrates with the Haio Admin API:

### Authentication
- Uses Swift-style authentication headers
- Format: `account:username` (e.g., `ali:ali`)
- Stores and manages auth tokens automatically

### Bucket Operations
- Lists containers/buckets via API
- Retrieves bucket metadata and statistics
- Real-time status updates

## Mount Options

The application uses optimized rclone mount options:

```bash
rclone mount 
    --daemon 
    --allow-non-empty 
    --dir-cache-time 10s 
    --poll-interval 1m 
    --vfs-cache-mode full 
    --vfs-cache-max-age 24h 
    --vfs-write-back 10s 
    --vfs-read-wait 20ms 
    --buffer-size 32M 
    --attr-timeout 1m 
    --cache-dir ~/.cache/rclone 
    {config_name}:{bucket} {mount_point}
```

## Systemd Service

For auto-mounting, the application creates systemd services:

### Service Location
```
/etc/systemd/system/haio-{username}-{bucket}.service
```

### Service Features
- Automatic startup after network is available
- Automatic restart on failure
- Proper cleanup on stop
- Environment variable configuration

## Troubleshooting

### Common Issues

#### Mount Fails
- Check if rclone is installed: `which rclone`
- Verify credentials are correct
- Ensure mount point directory exists
- Check for existing mounts: `mountpoint /mnt/haio-*`

#### Auto-mount Doesn't Work
- Verify sudo privileges
- Check systemd service status: `systemctl status haio-{username}-{bucket}`
- Review service logs: `journalctl -u haio-{username}-{bucket}`

#### Permission Denied
- Ensure user has access to mount points
- Check rclone configuration file permissions
- Verify API credentials

### Debug Mode
Run with debug output:
```bash
python3 main_new.py --debug
```

### Log Files
Application logs are written to:
- Console output during execution
- Systemd journal for auto-mount services

## Building from Source

### Development Setup
1. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install --upgrade pyinstaller
   ```

2. Build executable:
   ```bash
   pyinstaller --onefile --windowed --name "HaioDriveClient" main_new.py
   ```

### Creating Distribution
The build script handles:
- Virtual environment creation
- Dependency installation
- Executable building
- Desktop entry creation
- Permission setting

## Architecture

### Components
- **ApiClient**: Handles Haio API communication
- **RcloneManager**: Manages rclone operations and configuration
- **TokenManager**: Persistent credential storage
- **LoginDialog**: Beautiful authentication interface
- **BucketWidget**: Individual bucket management UI
- **HaioDriveClient**: Main application window

### Design Patterns
- Model-View separation
- Event-driven architecture
- Threaded operations for non-blocking UI
- Modular component design

## Security Considerations

### Credential Storage
- Tokens stored in user's home directory
- File permissions restricted to user only
- Consider encryption for production use

### Network Security
- HTTPS for all API communications
- Token-based authentication
- No password storage in memory

### System Access
- Minimal privilege requirements
- Sudo only for systemd service creation
- User-space mount operations

## Contributing

### Code Style
- Follow PEP 8 guidelines
- Use type hints where possible
- Document all public methods
- Maintain consistent naming

### Testing
- Test all mount/unmount operations
- Verify API integration
- Check UI responsiveness
- Validate error handling

## License

This project is part of the Haio smart cloud storage system.

## Support

For issues and support:
1. Check the troubleshooting section
2. Review application logs
3. Verify system requirements
4. Contact system administrator

## Pre-built Executables

Download the latest pre-built executable from the releases page:
- **Linux**: `S3DriveMounter` (single executable file)
- **Windows**: `S3DriveMounter.exe` (single executable file)

No installation or dependencies required - just download and run!

## Building from Source

### Requirements

- Python 3.8+
- FUSE (File System in User Space)
  - **Linux**: `sudo apt-get install fuse` (Ubuntu/Debian) or `sudo yum install fuse` (RHEL/CentOS)
  - **Windows**: Install WinFsp from https://github.com/billziss-gh/winfsp/releases

### Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd s3-drive-mounter
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Linux
   # or
   .venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running from Source

```bash
python main.py
```

### Building Executable

To create a standalone executable with all dependencies included:

**Linux:**
```bash
./build.sh
```

**Windows:**
```bash
build.bat
```

The executable will be created in the `dist/` directory and can be distributed without requiring Python or any dependencies to be installed on the target system.

## Usage

1. **Launch the application**:
   - From source: `python main.py`
   - From executable: `./dist/S3DriveMounter` (Linux) or `dist\S3DriveMounter.exe` (Windows)

2. **Enter AWS Credentials**:
   - AWS Access Key
   - AWS Secret Key (with show/hide toggle)
   - Select AWS Region

3. **Configure S3 Bucket**:
   - Enter S3 bucket name
   - Choose mount point (use Browse button for convenience)

4. **Test Connection** (optional but recommended):
   - Click "Test Connection" to verify your credentials and bucket access

5. **Mount the Drive**:
   - Click "Mount S3 Drive"
   - Monitor the log output for status updates
   - Access your S3 bucket contents through the mount point

6. **Unmount when done**:
   - Click "Unmount S3 Drive"
   - Or simply close the application (it will unmount automatically)

## System Requirements

### Linux
- FUSE installed (`sudo apt-get install fuse`)
- Mount permissions (may require running with sudo for some mount points)

### Windows
- WinFsp installed (https://github.com/billziss-gh/winfsp/releases)
- Administrator privileges may be required for some mount points

## AWS Permissions

Your AWS IAM user needs the following minimum permissions for the S3 bucket:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name",
                "arn:aws:s3:::your-bucket-name/*"
            ]
        }
    ]
}
```

## Security Features

- ✅ AWS credentials stored in memory only
- ✅ No credential persistence between sessions
- ✅ Password field masking with optional visibility toggle
- ✅ Secure connection testing before mounting
- ✅ Graceful unmounting on application exit

## Troubleshooting

### Common Issues

1. **Permission Denied**: Run with appropriate privileges or choose a mount point in your user directory
2. **FUSE/WinFsp Not Found**: Install the required filesystem driver for your platform
3. **Connection Failed**: Verify AWS credentials, region, and bucket permissions
4. **Mount Point Busy**: Ensure the directory is empty and not in use by other applications

### Log Output

The application provides real-time logging in the "Log Output" section. Monitor this for detailed information about operations and any errors.

## License

MIT License - see LICENSE file for details
# smartapp
