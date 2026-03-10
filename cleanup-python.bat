@echo off
setlocal enabledelayedexpansion
REM Clean up Python components while preserving as legacy option

echo ========================================
echo Cleaning Up Python Components
echo ========================================
echo.

echo This script will clean up Python-related files to transition to C version.
echo The Python version will be moved to a 'legacy' folder for reference.
echo.

set /p confirm="Are you sure you want to continue? (y/n): "
if /i not "!confirm!"=="y" (
    echo Cleanup cancelled.
    pause
    exit /b 0
)

echo.
echo Creating legacy folder...
if not exist "legacy" mkdir legacy

echo.
echo Moving Python files to legacy folder...

REM Move Python files
if exist "ttc.py" (
    echo Moving ttc.py to legacy/
    move "ttc.py" "legacy\"
)

if exist "requirements.txt" (
    echo Moving requirements.txt to legacy/
    move "requirements.txt" "legacy\"
)

if exist "build_exe.py" (
    echo Moving build_exe.py to legacy/
    move "build_exe.py" "legacy\"
)

if exist "README_PYTHON.md" (
    echo Moving README_PYTHON.md to legacy/
    move "README_PYTHON.md" "legacy\"
)

echo.
echo Moving Python-specific directories...

if exist "__pycache__" (
    echo Removing __pycache__/
    rmdir /s /q "__pycache__"
)

if exist "*.pyc" (
    echo Removing *.pyc files
    del *.pyc
)

echo.
echo Cleaning up Python build artifacts...

if exist "dist" (
    echo Removing dist/
    rmdir /s /q "dist"
)

if exist "build" (
    echo Removing build/
    rmdir /s /q "build"
)

if exist "*.spec" (
    echo Removing *.spec files
    del *.spec
)

echo.
echo Creating legacy documentation...

echo # Python Version (Legacy)> legacy\README_PYTHON.md
echo.>> legacy\README_PYTHON.md
echo This is the original Python version of Test Target Cropper.>> legacy\README_PYTHON.md
echo.>> legacy\README_PYTHON.md
echo ## Usage>> legacy\README_PYTHON.md
echo ```bash>> legacy\README_PYTHON.md
echo python ttc.py --help>> legacy\README_PYTHON.md
echo ```>> legacy\README_PYTHON.md
echo.>> legacy\README_PYTHON.md
echo ## Why Keep This?>> legacy\README_PYTHON.md
echo - Better DNG file compatibility>> legacy\README_PYTHON.md
echo - Reference implementation>> legacy\README_PYTHON.md
echo - Fallback for problematic files>> legacy\README_PYTHON.md

echo.
echo Cleanup complete!
echo.
echo Summary:
echo - Python files moved to legacy/ folder
echo - Build artifacts removed
echo - C version is now the primary implementation
echo - Python version preserved as legacy option
echo.

echo Current directory structure:
dir /b

echo.
echo Legacy folder contents:
if exist "legacy" dir /b legacy

pause
