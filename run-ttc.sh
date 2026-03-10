#!/bin/bash
# Run ttc.exe with proper VIPS library path for bash/WSL

echo "Setting up environment for Test Target Cropper (C Version)"
echo

# Set up library path for VIPS DLLs
export PATH="/c/vips/bin:$PATH"
export LD_LIBRARY_PATH="/c/vips/lib:$LD_LIBRARY_PATH"

echo "Environment configured for VIPS"
echo "PATH includes: /c/vips/bin"
echo

# Run ttc.exe with all arguments
./ttc.exe "$@"

echo
echo "Process complete"
