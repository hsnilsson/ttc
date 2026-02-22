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

def clean_build():
    """Clean previous build artifacts"""
    print("Cleaning previous build artifacts...")
    
    # Remove build directories
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Removed {dir_name}/")
    
    # Remove executable files
    for file_name in ['ttc.exe', 'ttc.spec']:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"Removed {file_name}")
    
    print("Clean complete!")

def build_executable():
    """Build standalone executable"""
    print("Building Test Target Cropper executable...")
    
    # Install dependencies (Pillow + rawpy for full-res DNG)
    print("Installing Pillow and rawpy...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "rawpy"])
    
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",           # Single executable
        "--console",           # Keep console window (fixes hanging)
        "--name=ttc",          # Output name
        "--distpath=dist",     # Output directory
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=PIL.ImageFilter",
        "--hidden-import=PIL.ImageFile",
        "--hidden-import=PIL.PngImagePlugin",
        "--hidden-import=rawpy",  # Full-resolution DNG
        "--hidden-import=numpy",
        "--collect-all=rawpy",    # Bundle libraw DLLs etc.
        "--noupx",
        "ttc.py"
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
    
    # Clean previous builds
    clean_build()
    
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
