@echo off
setlocal enabledelayedexpansion
REM Keep Python version as legacy option (less aggressive cleanup)

echo ========================================
echo Organizing Python Components as Legacy
echo ========================================
echo.

echo This script will organize Python components while keeping them available.
echo Python files will be moved to a 'legacy' folder but remain functional.
echo.

set /p confirm="Continue organizing Python components? (y/n): "
if /i not "!confirm!"=="y" (
    echo Organization cancelled.
    pause
    exit /b 0
)

echo.
echo Creating legacy folder...
if not exist "legacy" mkdir legacy

echo.
echo Moving Python files to legacy folder...

REM Move Python files (copy then delete to preserve)
if exist "ttc.py" (
    echo Copying ttc.py to legacy/
    copy "ttc.py" "legacy\" >nul
    echo Moving ttc.py to legacy/
    move "ttc.py" "legacy\" >nul
)

if exist "requirements.txt" (
    echo Copying requirements.txt to legacy/
    copy "requirements.txt" "legacy\" >nul
    echo Moving requirements.txt to legacy/
    move "requirements.txt" "legacy\" >nul
)

if exist "build_exe.py" (
    echo Copying build_exe.py to legacy/
    copy "build_exe.py" "legacy\" >nul
    echo Moving build_exe.py to legacy/
    move "build_exe.py" "legacy\" >nul
)

echo.
echo Creating legacy Python runner...

echo @echo off> legacy\run-python-ttc.bat
echo echo Running Python version of Test Target Cropper...>> legacy\run-python-ttc.bat
echo echo.>> legacy\run-python-ttc.bat
echo python ttc.py %%*>> legacy\run-python-ttc.bat

echo.
echo Creating legacy documentation...

echo # Python Version (Legacy)>> legacy\README_PYTHON.md
echo.>> legacy\README_PYTHON.md
echo This is the original Python version of Test Target Cropper, preserved for:>> legacy\README_PYTHON.md
echo.>> legacy\README_PYTHON.md
echo ## Use Cases>> legacy\README_PYTHON.md
echo - **DNG files with compatibility issues** - Better DNG support via rawpy>> legacy\README_PYTHON.md
echo - **Reference implementation** - Compare with C version>> legacy\README_PYTHON.md
echo - **Fallback option** - When C version doesn't work>> legacy\README_PYTHON.md
echo.>> legacy\README_PYTHON.md
echo ## Usage>> legacy\README_PYTHON.md
echo ```bash>> legacy\README_PYTHON.md
echo # From this directory>> legacy\README_PYTHON.md
echo run-python-ttc.bat --help>> legacy\README_PYTHON.md
echo.>> legacy\README_PYTHON.md
echo # Or directly>> legacy\README_PYTHON.md
echo python ttc.py --help>> legacy\README_PYTHON.md
echo ```>> legacy\README_PYTHON.md
echo.>> legacy\README_PYTHON.md
echo ## Installation>> legacy\README_PYTHON.md
echo ```bash>> legacy\README_PYTHON.md
echo pip install -r requirements.txt>> legacy\README_PYTHON.md
echo ```>> legacy\README_PYTHON.md

echo.
echo Organization complete!
echo.
echo Summary:
echo - Python files organized in legacy/ folder
echo - C version remains primary implementation
echo - Python version available as legacy option
echo - Both versions remain functional
echo.

echo To run Python version:
echo   legacy\run-python-ttc.bat --help
echo.

echo To run C version:
echo   ttc.exe --help

pause
