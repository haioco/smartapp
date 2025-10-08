# PowerShell build script for Smart HAIO App on Windows
# This handles Python PATH issues better than batch files

Write-Host "Building Smart HAIO App for Windows..." -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.9+ from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
try {
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install PyInstaller
Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
try {
    python -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller install failed" }
    Write-Host "✓ PyInstaller installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install PyInstaller" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Clean previous builds
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }

# Build the application
Write-Host "Building Windows executable..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Cyan

try {
    # Use python -m PyInstaller to avoid PATH issues
    python -m PyInstaller s3_mounter_windows_simple.spec --clean --noconfirm
    if ($LASTEXITCODE -ne 0) { 
        throw "Build failed" 
    }
    
    # Check if executable was created
    if (Test-Path "dist\HaioSmartApp.exe") {
        Write-Host "✓ Build completed successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Executable location: dist\HaioSmartApp.exe" -ForegroundColor Cyan
        
        # Get file size
        $fileSize = (Get-Item "dist\HaioSmartApp.exe").Length / 1MB
        Write-Host "Executable size: $([math]::Round($fileSize, 1)) MB" -ForegroundColor Cyan
        
    } else {
        throw "Executable not found after build"
    }
    
} catch {
    Write-Host "❌ Build failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting tips:" -ForegroundColor Yellow
    Write-Host "1. Make sure you're running as Administrator" -ForegroundColor White
    Write-Host "2. Try installing Python from python.org (not Windows Store)" -ForegroundColor White
    Write-Host "3. Check antivirus isn't blocking the build process" -ForegroundColor White
    Read-Host "Press Enter to exit"
    exit 1
}

# Check for WinFsp
Write-Host ""
Write-Host "Checking for WinFsp installation..." -ForegroundColor Yellow
$winfspPaths = @(
    "C:\Program Files\WinFsp",
    "C:\Program Files (x86)\WinFsp",
    "$env:ProgramFiles\WinFsp",
    "${env:ProgramFiles(x86)}\WinFsp"
)

$winfspFound = $false
foreach ($path in $winfspPaths) {
    if (Test-Path $path) {
        Write-Host "✓ WinFsp found at: $path" -ForegroundColor Green
        $winfspFound = $true
        break
    }
}

if (-not $winfspFound) {
    Write-Host "⚠️  WARNING: WinFsp not detected!" -ForegroundColor Yellow
    Write-Host "Please install WinFsp from: https://winfsp.dev/rel/" -ForegroundColor Cyan
    Write-Host "This is required for mounting S3 buckets on Windows." -ForegroundColor White
}

Write-Host ""
Write-Host "🎉 Build completed successfully!" -ForegroundColor Green
Write-Host "You can now run: dist\HaioSmartApp.exe" -ForegroundColor Cyan
Write-Host ""
Write-Host "Features included in this build:" -ForegroundColor Yellow
Write-Host "  ✓ Enhanced Windows mounting with WinFsp detection" -ForegroundColor White
Write-Host "  ✓ Windows auto-mount using Task Scheduler" -ForegroundColor White
Write-Host "  ✓ Cross-platform compatibility" -ForegroundColor White
Write-Host "  ✓ Improved error logging and debugging" -ForegroundColor White
Write-Host "  ✓ Modern PyQt6 interface" -ForegroundColor White

Read-Host "Press Enter to exit"
