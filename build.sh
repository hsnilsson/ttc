#!/bin/bash
# Build script for Test Target Cropper on Unix-like systems

set -e

echo "Building Test Target Cropper..."

# Check for required dependencies
if ! command -v pkg-config &> /dev/null; then
    echo "ERROR: pkg-config not found. Please install it."
    echo "On Ubuntu/Debian: sudo apt-get install pkg-config"
    echo "On macOS: brew install pkg-config"
    exit 1
fi

if ! pkg-config --exists vips; then
    echo "ERROR: VIPS library not found. Please install it."
    echo "On Ubuntu/Debian: sudo apt-get install libvips-dev"
    echo "On macOS: brew install vips"
    echo "On other systems: https://libvips.github.io/libvips/install.html"
    exit 1
fi

# Get compiler flags
CFLAGS=$(pkg-config --cflags vips)
LDFLAGS=$(pkg-config --libs vips)

echo "Compiler flags: $CFLAGS"
echo "Linker flags: $LDFLAGS"

# Build
gcc -Wall -O2 -std=c99 $CFLAGS ttc.c -o ttc $LDFLAGS

if [ $? -eq 0 ]; then
    echo "Build successful! ttc executable created."
    echo ""
    echo "Testing ttc:"
    ./ttc --version
    ./ttc --help
else
    echo "Build failed!"
    exit 1
fi
