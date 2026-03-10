# Development Setup Guide

This guide helps developers set up the Test Target Cropper C implementation from scratch.

## Quick Setup

Run the complete setup script:
```cmd
setup-dev.bat
```

This will:
1. Install VIPS library (latest version)
2. Install w64devkit (C compiler)
3. Build and test ttc.exe

## Manual Setup

### 1. Install VIPS Library

```cmd
setup-vips.bat
```

This automatically downloads and installs the latest VIPS library from:
https://github.com/libvips/build-win64-mxe/releases

### 2. Install C Compiler

```cmd
install-w64devkit.bat
```

This downloads and sets up w64devkit (portable GCC for Windows).

### 3. Build ttc.exe

```cmd
build-w64devkit.bat
```

### 4. Test Installation

```cmd
./ttc-bash --help
./ttc-bash .
```

## Development Workflow

### Building
```cmd
# Build the C version
build-w64devkit.bat

# Build release version
build-final-release.bat
```

### Testing
```cmd
# Test with DNG files
./ttc-bash .

# Test with PNG files only
./ttc-bash --use-pngs-only .

# Test help
./ttc-bash --help

# Test version
./ttc-bash --version
```

### Running from Different Shells
```cmd
# Windows Command Prompt
ttc.exe --help

# Windows PowerShell
./ttc.exe --help

# Bash/WSL
./ttc-bash --help
```

## Project Structure

```
ttc/
├── ttc-fixed.c              # Main C source code
├── ttc.exe                  # Compiled executable
├── build-w64devkit.bat      # Build script
├── setup-vips.bat           # VIPS setup script
├── setup-dev.bat            # Complete setup script
├── run-ttc-bash.bat         # Bash runner
├── ttc-bash                 # Bash wrapper
├── DNG_COMPATIBILITY.md     # DNG troubleshooting
└── README_DEVELOPMENT.md    # This file
```

## Dependencies

### VIPS Library
- **Source:** https://github.com/libvips/build-win64-mxe
- **Version:** Latest (auto-detected)
- **Location:** C:\vips
- **Required for:** Image processing (DNG, PNG support)

### w64devkit
- **Source:** https://github.com/skeeto/w64devkit
- **Version:** v1.2.0
- **Location:** ./w64devkit
- **Required for:** C compilation

## Troubleshooting

### VIPS Issues
```cmd
# Reinstall VIPS
setup-vips.bat

# Check VIPS installation
C:\vips\bin\vips.exe --version
```

### Build Issues
```cmd
# Check w64devkit
w64devkit\bin\gcc.exe --version

# Rebuild
build-w64devkit.bat
```

### DNG Loading Issues
See: [DNG_COMPATIBILITY.md](DNG_COMPATIBILITY.md)

## Environment Variables

The setup scripts automatically configure:
- `PATH` includes `C:\vips\bin` and `./w64devkit/bin`
- VIPS library paths are configured in build scripts

## Contributing

1. Fork the repository
2. Set up development environment with `setup-dev.bat`
3. Make changes to `ttc-fixed.c`
4. Test with `build-w64devkit.bat` and `./ttc-bash .`
5. Submit pull request

## Support

- **Issues:** https://github.com/hsnilsson/ttc/issues
- **Documentation:** README.md
- **DNG Issues:** DNG_COMPATIBILITY.md
