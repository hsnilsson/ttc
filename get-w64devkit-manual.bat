@echo off
echo ========================================
echo Manual w64devkit Download Instructions
echo ========================================
echo.
echo Due to download issues, please follow these steps:
echo.
echo 1. Open your web browser
echo 2. Go to: https://github.com/skeeto/w64devkit/releases
echo 3. Download: w64devkit-1.2.0.tar.gz
echo 4. Save the file to: %CD%
echo 5. Run this script again to extract
echo.
echo Alternative: Try the zip version
echo 1. Go to: https://github.com/skeeto/w64devkit/releases
echo 2. Download: w64devkit-1.2.0.zip
echo 3. Save as: w64devkit.zip
echo 4. Run: tar -xf w64devkit.zip
echo.
echo Checking for existing downloads...

if exist "w64devkit-1.2.0.tar.gz" (
    echo Found w64devkit-1.2.0.tar.gz
    echo Extracting...
    tar -xf w64devkit-1.2.0.tar.gz
    if exist "w64devkit\bin\gcc.exe" (
        echo SUCCESS! w64devkit extracted
        del w64devkit-1.2.0.tar.gz
    )
)

if exist "w64devkit.zip" (
    echo Found w64devkit.zip
    echo Extracting...
    tar -xf w64devkit.zip
    if exist "w64devkit\bin\gcc.exe" (
        echo SUCCESS! w64devkit extracted
        del w64devkit.zip
    )
)

if exist "w64devkit\bin\gcc.exe" (
    echo.
    echo w64devkit is ready! You can now run build-simple.bat
) else (
    echo.
    echo w64devkit not found. Please download manually as instructed above.
)

pause
