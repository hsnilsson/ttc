@echo off
setlocal enabledelayedexpansion
REM Setup script for developers - downloads and installs latest VIPS

echo ========================================
echo VIPS Setup for Test Target Cropper
echo ========================================
echo.

echo This script downloads and installs the latest VIPS library
echo for the Test Target Cropper C implementation.
echo.

REM Check if VIPS is already installed and working
if exist "C:\vips\bin\vips.exe" (
    echo Testing existing VIPS installation...
    C:\vips\bin\vips.exe --version >nul 2>&1
    if not errorlevel 1 (
        echo VIPS is already installed and working!
        echo Version:
        C:\vips\bin\vips.exe --version
        echo.
        echo You can rebuild ttc.exe with:
        echo   build-w64devkit.bat
        echo.
        set /p reinstall="Do you want to reinstall anyway? (y/n): "
        if /i not "!reinstall!"=="y" (
            pause
            exit /b 0
        )
    )
)

echo.
echo Getting latest VIPS version information...
echo.

REM Use GitHub API to get the latest release
powershell -Command "
try {
    $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/libvips/build-win64-mxe/releases/latest' -Headers @{'Accept'='application/vnd.github.v3+json'}
    $version = $release.tag_name
    $downloadUrl = $release.assets | Where-Object {$_.name -like 'vips-dev-w64-all-*.zip'} | Select-Object -First 1 -ExpandProperty browser_download_url
    Write-Output \"Latest version: $version\"
    Write-Output \"Download URL: $downloadUrl\"
    $version | Out-File -FilePath 'vips-version.txt' -Encoding utf8
    $downloadUrl | Out-File -FilePath 'vips-download.txt' -Encoding utf8
} catch {
    Write-Output \"Failed to get latest version, using fallback\"
    Write-Output \"v8.18.0\" | Out-File -FilePath 'vips-version.txt' -Encoding utf8
    Write-Output \"https://github.com/libvips/build-win64-mxe/releases/download/v8.18.0/vips-dev-w64-all-8.18.0.zip\" | Out-File -FilePath 'vips-download.txt' -Encoding utf8
}
"

if not exist "vips-version.txt" (
    echo ERROR: Failed to get version information
    pause
    exit /b 1
)

set /p version=<vips-version.txt
set /p downloadUrl=<vips-download.txt

echo Latest VIPS version: %version%
echo.

REM Remove any existing VIPS installation
if exist "C:\vips" (
    echo Removing existing VIPS installation...
    rmdir /s /q "C:\vips"
)

echo.
echo Downloading VIPS %version%...
echo This may take a few minutes...
echo.

REM Download the VIPS package
echo Downloading from: %downloadUrl%
curl -L --retry 3 --retry-delay 10 --show-error -o "vips-dev-w64-all-%version%.zip" "%downloadUrl%"

if not exist "vips-dev-w64-all-%version%.zip" (
    echo ERROR: Failed to download VIPS
    echo.
    echo Manual download required:
    echo 1. Visit: https://github.com/libvips/build-win64-mxe/releases/tag/%version%
    echo 2. Download: vips-dev-w64-all-%version%.zip
    echo 3. Save to: %CD%
    echo 4. Run this script again
    pause
    exit /b 1
)

echo.
echo Download successful!
echo.

echo Checking file integrity...
for %%I in ("vips-dev-w64-all-%version%.zip") do set size=%%~zI
echo File size: %size% bytes

if %size% LSS 10000000 (
    echo ERROR: Downloaded file is too small (%size% bytes)
    echo Expected at least 10 MB - download probably failed
    del "vips-dev-w64-all-%version%.zip"
    pause
    exit /b 1
)

echo File size looks good.
echo.

echo Extracting VIPS...
echo This may take a minute...

REM Try multiple extraction methods
echo Trying Python extraction...
python -c "
import zipfile
import sys
import os

try:
    print('Extracting with Python zipfile...')
    with zipfile.ZipFile('vips-dev-w64-all-%version%.zip', 'r') as zip_ref:
        zip_ref.extractall('C:\\')
    print('Extraction successful!')
    
    if os.path.exists('C:\\vips\\bin\\vips.exe'):
        print('VIPS executable found!')
    else:
        print('ERROR: VIPS executable not found')
        sys.exit(1)
        
except Exception as e:
    print(f'Python extraction failed: {e}')
    sys.exit(1)
"

if not errorlevel 1 (
    goto test_vips
)

echo Python extraction failed, trying 7-Zip...
7z x "vips-dev-w64-all-%version%.zip" -oC:\ >nul 2>&1

if exist "C:\vips\bin\vips.exe" (
    echo 7-Zip extraction successful!
    goto test_vips
)

echo 7-Zip failed, trying tar...
tar -xf "vips-dev-w64-all-%version%.zip" -C C:\

if exist "C:\vips\bin\vips.exe" (
    echo tar extraction successful!
    goto test_vips
)

echo All extraction methods failed!
echo Trying PowerShell as last resort...
powershell -Command "Expand-Archive -Path 'vips-dev-w64-all-%version%.zip' -DestinationPath 'C:\' -Force"

if not exist "C:\vips\bin\vips.exe" (
    echo ERROR: All extraction methods failed
    echo Please extract manually and try again
    pause
    exit /b 1
)

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
echo Verifying installation components...

REM Check essential files
set "errors=0"

if not exist "C:\vips\lib\libvips.lib" (
    echo ERROR: VIPS library missing
    set "errors=1"
)

if not exist "C:\vips\include\vips\vips.h" (
    echo ERROR: VIPS headers missing
    set "errors=1"
)

if not exist "C:\vips\bin\libvips-42.dll" (
    echo ERROR: VIPS DLL missing
    set "errors=1"
)

if not exist "C:\vips\bin\libglib-2.0-0.dll" (
    echo ERROR: GLib DLL missing
    set "errors=1"
)

if %errors% GTR 0 (
    echo ERROR: Some components missing
    echo Available files in C:\vips\bin:
    dir C:\vips\bin\*.dll | findstr -i "vips\|glib"
    pause
    exit /b 1
)

echo.
echo Cleaning up...
del "vips-dev-w64-all-%version%.zip" 2>nul
del vips-version.txt 2>nul
del vips-download.txt 2>nul

echo.
echo ========================================
echo VIPS Setup Complete!
echo ========================================
echo.
echo SUCCESS! VIPS %version% has been installed.
echo.
echo Next steps:
echo 1. Build ttc.exe:    build-w64devkit.bat
echo 2. Test with DNG:    ./ttc-bash .
echo 3. Test help:        ./ttc-bash --help
echo.

echo Installation details:
echo - VIPS version: %version%
echo - Location: C:\vips
echo - Executable: C:\vips\bin\vips.exe
echo.

echo Ready for Test Target Cropper C development!
pause
