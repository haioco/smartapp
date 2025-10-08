#!/bin/bash

# Build script using Docker for Debian 12 compatibility

echo "Building HaioSmartApp for Debian 12 compatibility using Docker..."
echo "================================================================="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Installation: sudo apt update && sudo apt install docker.io"
    exit 1
fi

# Build the Docker image
echo "🔨 Building Docker image for Debian 12..."
docker build -f Dockerfile.debian12 -t haiosmartapp-debian12 .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

# Create output directory
mkdir -p dist-debian12

# Run the container and copy the built application
echo "📦 Extracting built application..."
docker run --rm -v $(pwd)/dist-debian12:/output haiosmartapp-debian12

# Check if build was successful
if [ -f "dist-debian12/HaioSmartApp" ]; then
    echo "✅ Debian 12 compatible build created successfully!"
    echo "📍 Location: dist-debian12/HaioSmartApp"
    echo ""
    echo "🧪 Testing GLIBC requirements:"
    objdump -T dist-debian12/HaioSmartApp | grep GLIBC | sort -V | tail -3
    echo ""
    echo "🚀 Ready to run on Debian 12!"
else
    echo "❌ Build failed - no executable found"
    exit 1
fi

# Clean up Docker image (optional)
read -p "🗑️  Remove Docker build image? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker rmi haiosmartapp-debian12
    echo "✅ Docker image removed"
fi
