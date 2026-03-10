@echo off
REM Download and install Visual Studio Build Tools

echo Installing Visual Studio Build Tools for Test Target Cropper...
echo.

echo This will download Visual Studio Build Tools installer.
echo You will need to select "C++ build tools" during installation.
echo.

REM Download Visual Studio Build Tools installer
echo Downloading Visual Studio Build Tools installer...
curl -L -o vs_buildtools.exe "https://aka.ms/vs/17/release/vs_buildtools.exe"

if not exist "vs_buildtools.exe" (
    echo Failed to download installer.
    echo Please download manually from: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio
    pause
    exit /b 1
)

echo.
echo Starting installer...
echo.
echo IMPORTANT: In the installer, select:
echo   - "C++ build tools" workload
echo   - Check "MSVC v143 - VS 2022 C++ x64/x86 build tools"
echo   - Check "Windows 10/11 SDK" (latest version)
echo.
echo After installation completes, run: build.bat
echo.

vs_buildtools.exe

if errorlevel 1 (
    echo Installation may have failed. Please try manual installation.
    pause
    exit /b 1
)

echo.
echo Installation complete! You can now run build.bat to compile ttc.exe
echo.

pause
