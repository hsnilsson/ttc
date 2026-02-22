#!/bin/bash
# Test Target Cropper - Unix/Linux/macOS Installation Script
# Installs ttc command to system PATH

set -e

echo "Installing Test Target Cropper (ttc)..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3.7+ first: https://www.python.org/downloads/"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "Error: pip is required but not installed."
    echo "Please install pip first."
    exit 1
fi

# Install Pillow
echo "Installing Pillow..."
python3 -m pip install --user Pillow || python -m pip install --user Pillow

# Create installation directory
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

# Copy files
echo "Installing ttc to $INSTALL_DIR..."
cp ttc.py "$INSTALL_DIR/ttc.py"
cp ttc "$INSTALL_DIR/ttc"
chmod +x "$INSTALL_DIR/ttc"

# Add to PATH if not already there
SHELL_RC=""
if [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.profile" ]; then
    SHELL_RC="$HOME/.profile"
fi

if [ -n "$SHELL_RC" ] && ! grep -q "$INSTALL_DIR" "$SHELL_RC"; then
    echo "Adding $INSTALL_DIR to PATH in $SHELL_RC..."
    echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$SHELL_RC"
    echo "Added to PATH. Please run: source $SHELL_RC"
fi

echo ""
echo "Installation complete!"
echo ""
echo "Usage:"
echo "  ttc                    # Process current directory"
echo "  ttc ../photos          # Process parent directory"
echo "  ttc --help             # Show help"
echo ""
echo "If command not found, restart your terminal or run:"
echo "  export PATH=\"\$PATH:$INSTALL_DIR\""
