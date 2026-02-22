# Contributing to RawTherapee Composite Generator

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## How to Contribute

### Reporting Issues

1. Use the [GitHub Issues](https://github.com/yourusername/rawtherapee-composite-generator/issues) page
2. Provide detailed information about the issue:
   - Operating system and Python version
   - Steps to reproduce the problem
   - Expected vs actual behavior
   - Any error messages

### Feature Requests

1. Open an issue with the "enhancement" label
2. Describe the feature and why it would be useful
3. Provide examples of how you'd like it to work

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly on different platforms if possible
5. Commit your changes with clear messages
6. Push to your fork: `git push origin feature-name`
7. Open a pull request

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/rawtherapee-composite-generator.git
   cd rawtherapee-composite-generator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run tests:
   ```bash
   python create_composite.py --help
   ```

## Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep lines under 100 characters
- Use type hints where appropriate

## Testing

- Test with different image sizes and formats
- Verify cross-platform compatibility
- Test command-line arguments
- Check error handling

## Submitting Changes

1. Ensure your code follows the style guidelines
2. Add tests for new features
3. Update documentation if needed
4. Commit with descriptive messages
5. Submit a pull request with a clear description

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions

Feel free to open an issue if you have questions about contributing!
