# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-22

### Added

- Initial release of Vlad's Test Target Cropper
- Composite image creation from Vlad's test target photos
- 2x2 grid layout with corner crops and center overlay
- Pixel-perfect output (no compression, no interpolation)
- Configurable crop positions via percentages
- Batch processing of multiple PNG files
- Large image support (handles high-resolution outputs)
- Flexible input/output directory specification
- Command-line interface with help system
- Cross-platform compatibility (Windows, Mac, Linux)
- Smart output placement (default: INPUT_DIR/crops/)
- Automatic output directory creation
- Professional error handling and validation
- Version information display (-v/--version)

### Features

- Corner crops: 7% of image height, square format
- Center crop: configurable rectangular area (default: 58%-61% H, 37%-42% V)
- Output format: PNG with maximum quality settings
- Excludes existing composite/crop files from processing
- Detailed progress reporting and statistics

### Purpose

- Perfect for analyzing lens sharpness, resolution, and optical performance
- Designed specifically for Vlad's test target photos
- Ideal for pixel peeping and detailed image analysis

### Documentation

- Comprehensive README with usage examples
- Command-line help with examples
- Configuration guide with percentage coordinates
- TODO list for future improvements
- MIT License

### Technical

- Python 3.7+ compatibility
- Pillow (PIL) imaging library dependency
- Argument parsing with argparse
- Proper exit codes and error handling
- Cross-platform path handling
