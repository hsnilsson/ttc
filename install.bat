@echo off
REM Test Target Cropper - Windows Installation Script
REM Installs ttc command to system PATH

echo Installing Test Target Cropper (ttc)...

REM Check if Python 3 is installed (try multiple commands)
echo Checking for Python 3...

py --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=2" %%i in ('py --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo %PYTHON_VERSION% | findstr "3." >nul
    if not errorlevel 1 (
        set PYTHON_CMD=py
        goto :python_found
    )
)

python3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python3
    goto :python_found
)

python --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo %PYTHON_VERSION% | findstr "3." >nul
    if not errorlevel 1 (
        set PYTHON_CMD=python
        goto :python_found
    )
)

echo Error: Python 3 is required but not found in PATH.
echo Found Python commands may be Python 2.7.
echo Please install Python 3.7+ first: https://www.python.org/downloads/
echo Make sure to add Python to PATH during installation.
pause
exit /b 1

:python_found
echo Found Python: %PYTHON_CMD%
%PYTHON_CMD% --version

REM Check if pip is available (use same Python command)
%PYTHON_CMD% -m pip --version >nul 2>&1
if errorlevel 1 (
    echo Error: pip is required but not installed.
    echo Please install pip first.
    pause
    exit /b 1
)

REM Install Pillow
echo Installing Pillow...
%PYTHON_CMD% -m pip install --user Pillow

REM Create installation directory
set INSTALL_DIR=%USERPROFILE%\ttc
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy files
echo Installing ttc to %USERPROFILE%\ttc...
copy ttc.py "%USERPROFILE%\ttc\ttc.py" >nul
copy ttc "%USERPROFILE%\ttc\ttc" >nul

REM Add to PATH
echo Adding to system PATH...
setx PATH "%PATH%;%USERPROFILE%\ttc" >nul

REM Create batch wrapper
echo @echo off > "%USERPROFILE%\ttc\ttc.bat"
echo %PYTHON_CMD% "%USERPROFILE%\ttc\ttc.py" %%* >> "%USERPROFILE%\ttc\ttc.bat"

REM Copy to user directory instead of system32 (avoids admin rights)
echo Creating user command...
copy "%USERPROFILE%\ttc\ttc.bat" "%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\ttc.bat" >nul 2>&1
if errorlevel 1 (
    echo User installation complete!
    echo.
    echo Usage:
    echo   ttc                    # Process current directory
    echo   ttc ..\photos         # Process parent directory
    echo   ttc --help            # Show help
    echo.
    echo If command not found, restart Command Prompt or PowerShell.
) else (
    echo Installation complete!
    echo.
    echo Usage:
    echo   ttc                    # Process current directory
    echo   ttc ..\photos         # Process parent directory
    echo   ttc --help            # Show help
)

pause
