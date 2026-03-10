@echo off
setlocal enabledelayedexpansion
REM Install VIPS using build-win64-mxe distribution (proper Windows build)

echo ========================================
echo Installing VIPS (build-win64-mxe)
echo ========================================
echo.

echo Using the proper Windows VIPS distribution...
echo.

REM Remove any existing corrupted VIPS installation
if exist "C:\vips" (
    echo Removing old VIPS installation...
    rmdir /s /q "C:\vips"
)

echo.
echo Opening VIPS download page in your browser...
echo.

REM Open the build-win64-mxe releases page
start https://github.com/libvips/build-win64-mxe/releases/tag/v8.18.0

echo.
echo INSTRUCTIONS:
echo ============
echo 1. On the GitHub page, download: vips-dev-w64-all-8.18.0.zip
echo 2. Save it in this directory: %CD%
echo 3. Run this script again (it will auto-install)
echo.

echo The file should be around 50-100 MB in size.
echo.

if not exist "vips-dev-w64-all-8.18.0.zip" (
    echo Waiting for download...
    echo Once downloaded, press any key to continue...
    pause
)

if not exist "vips-dev-w64-all-8.18.0.zip" (
    echo ERROR: vips-dev-w64-all-8.18.0.zip not found
    echo Please download it first
    pause
    exit /b 1
)

echo.
echo Found vips-dev-w64-all-8.18.0.zip
echo.

echo Checking file integrity...
for %%I in (vips-dev-w64-all-8.18.0.zip) do set size=%%~zI
echo File size: %size% bytes

if %size% LSS 10000000 (
    echo ERROR: File is too small (%size% bytes)
    echo Expected at least 10 MB
    echo The download probably failed
    pause
    exit /b 1
)

echo File size looks good.
echo.

echo Extracting VIPS...
echo This may take a minute...

REM Try Python extraction first (most reliable)
python -c "
import zipfile
import sys
import os

try:
    print('Extracting with Python zipfile...')
    with zipfile.ZipFile('vips-dev-w64-all-8.18.0.zip', 'r') as zip_ref:
        zip_ref.extractall('C:\\')
    print('Extraction successful!')
    
    # Check if VIPS was extracted
    if os.path.exists('C:\\vips\\bin\\vips.exe'):
        print('VIPS executable found!')
    else:
        print('ERROR: VIPS executable not found after extraction')
        print('Contents of C:\\:')
        for item in os.listdir('C:\\'):
            print(f'  {item}')
        sys.exit(1)
        
except Exception as e:
    print(f'Python extraction failed: {e}')
    sys.exit(1)
"

if not errorlevel 1 (
    echo Python extraction successful!
    goto test_vips
)

echo Python extraction failed, trying 7-Zip...
7z x vips-dev-w64-all-8.18.0.zip -oC:\ >nul 2>&1

if exist "C:\vips\bin\vips.exe" (
    echo 7-Zip extraction successful!
    goto test_vips
)

echo 7-Zip failed, trying tar...
tar -xf vips-dev-w64-all-8.18.0.zip -C C:\

if exist "C:\vips\bin\vips.exe" (
    echo tar extraction successful!
    goto test_vips
)

echo All extraction methods failed!
echo Checking what was extracted...
dir C:\ | findstr vips
pause
exit /b 1

:test_vips
echo.
echo Testing VIPS installation...
C:\vips\bin\vips.exe --version

if errorlevel 1 (
    echo ERROR: VIPS test failed
    pause
    exit /b 1
)

echo.
echo Checking library files...
if not exist "C:\vips\lib\libvips.lib" (
    echo ERROR: VIPS library missing
    echo Available libraries:
    dir C:\vips\lib\*.lib
    pause
    exit /b 1
)

if not exist "C:\vips\include\vips\vips.h" (
    echo ERROR: VIPS headers missing
    echo Available headers:
    dir C:\vips\include\vips\*.h
    pause
    exit /b 1
)

echo.
echo Checking DLL files...
if not exist "C:\vips\bin\libvips-42.dll" (
    echo ERROR: VIPS DLL missing
    echo Available DLLs:
    dir C:\vips\bin\*.dll | findstr vips
    pause
    exit /b 1
)

echo.
echo Cleaning up...
del vips-dev-w64-all-8.18.0.zip

echo.
echo ========================================
echo VIPS Installation Complete!
echo ========================================
echo.
echo SUCCESS! VIPS has been properly installed using build-win64-mxe.
echo.
echo Now rebuild ttc.exe:
echo   build-w64devkit.bat
echo.
echo Then test your DNG file:
echo   ./ttc-bash .
echo.

pause
