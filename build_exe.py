#!/usr/bin/env python3
"""
Build standalone executable for Test Target Cropper
Creates ttc.exe that doesn't require Python installation
"""

import os
import sys
import subprocess
import shutil

def install_pyinstaller():
    """Install PyInstaller if not present"""
    try:
        import PyInstaller
        print("PyInstaller already installed")
        return True
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True

def build_executable():
    """Build standalone executable"""
    print("Building Test Target Cropper executable...")
    
    # Install Pillow first
    print("Installing Pillow...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",           # Single executable
        "--console",           # Keep console window (fixes argparse output)
        "--name=ttc",          # Output name
        "--distpath=dist",       # Output directory
        "--hidden-import=PIL",  # Include PIL/Pillow
        "--hidden-import=PIL.Image",
        "--hidden-import=PIL.ImageFilter",
        "ttc.py"               # Input script
    ]
    
    try:
        subprocess.check_call(cmd)
        print("Build successful!")
        print(f"Executable created: dist/ttc.exe")
        
        # Copy to current directory
        if os.path.exists("dist/ttc.exe"):
            shutil.copy("dist/ttc.exe", "ttc.exe")
            print("Copied to current directory: ttc.exe")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False

def main():
    """Main build process"""
    print("Test Target Cropper - Executable Builder")
    print("=" * 50)
    
    # Check if ttc.py exists
    if not os.path.exists("ttc.py"):
        print("Error: ttc.py not found in current directory")
        return 1
    
    # Install PyInstaller
    if not install_pyinstaller():
        print("Failed to install PyInstaller")
        return 1
    
    # Build executable
    if not build_executable():
        print("Failed to build executable")
        return 1
    
    print("\nBuild complete!")
    print("You can now distribute ttc.exe without requiring Python installation")
    return 0

if __name__ == "__main__":
    exit(main())
