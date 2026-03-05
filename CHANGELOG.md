# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-03-05

### Added

- Parallel processing for multiple images using ThreadPoolExecutor
- Configurable worker count with `-j/--jobs` flag (default: CPU count)
- Coordinate caching with `@lru_cache` decorator for repeated calculations
- Explicit memory management with image cleanup to reduce memory usage
- Intelligent memory monitoring with psutil (optional dependency)
- Adaptive resource scaling based on memory usage and CPU cores
- Memory-efficient RAW processing settings to prevent exhaustion

### Performance

- 2-8x faster processing for multiple images (depending on CPU cores)
- Lower memory footprint with proper resource cleanup
- Reduced CPU overhead from cached crop coordinate calculations
- Adaptive worker scaling: uses all cores except one (avoids 100% CPU)
- Memory thresholds: 90% usage warning, adaptive throttling at 60%/80%

### Changed

- Updated version to 1.3.0
- Optimized `create_composite_layout()` function with cached coordinates
- Refactored `process_all_files()` to support parallel execution
- Memory-efficient RAW demosaic algorithm (LINEAR instead of default)
- Graceful fallback when psutil is not available
- Conservative CPU usage to maintain system responsiveness

## [1.2.0] - 2026-02-22

### Changed

- Updated contribution guidelines
- More pristine output - still needs to be confirmed

### Removed

- Removed TODO list from changelog (moved to project tracking)

## [1.0.1] - 2026-02-22

### Fixed

- Minor documentation updates

## [1.0.0] - 2026-02-22

### Added

- Initial release of Test Target Cropper
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
- Error handling and validation
- Version information display (-v/--version)

### Features

- Corner crops: 7% of image height, square format
- Center crop: configurable rectangular area (default: 58%-61% H, 37%-42% V)
- Output format: PNG with maximum quality settings
- Excludes existing composite/crop files from processing
- Detailed progress reporting and statistics

### Purpose

- Perfect for analyzing lens sharpness, resolution, and optical performance
- Designed mainly for Vlad's test target photos
- Ideal for pixel peeping and detailed image analysis

### Documentation

- Comprehensive README with usage examples
- Command-line help with examples
- Configuration guide with percentage coordinates
- MIT License

### Technical

- Python 3.7+ compatibility
- Pillow (PIL) imaging library dependency
- Argument parsing with argparse
- Proper exit codes and error handling
- Cross-platform path handling
