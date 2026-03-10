@echo off
setlocal enabledelayedexpansion
REM Create release package for Test Target Cropper (C Version)

echo ========================================
echo Creating Release Package
echo ========================================
echo.

REM Build the final release version first
echo Building release version...
call build-final-release.bat

if not exist "ttc.exe" (
    echo ERROR: ttc.exe not found. Build failed.
    pause
    exit /b 1
)

echo.
echo Creating release package...
echo.

REM Create release directory
if exist "release" rmdir /s /q "release"
mkdir release
mkdir release\bin
mkdir release\docs
mkdir release\scripts

echo Copying executable...
copy "ttc.exe" "release\bin\"

echo Copying documentation...
copy "README.md" "release\docs\"
copy "DNG_COMPATIBILITY.md" "release\docs\"
copy "INSTALL_WINDOWS.md" "release\docs\" 2>nul
copy "LICENSE" "release\docs\" 2>nul

echo Copying scripts...
copy "run-ttc-release.bat" "release\scripts\"
copy "build-final-release.bat" "release\scripts\"

echo Copying source code...
if not exist "release\src" mkdir release\src
copy "ttc-fixed.c" "release\src\"
copy "Makefile" "release\src\" 2>nul

echo Creating VIPS DLL collection script...
echo @echo off> release\scripts\copy-vips-dlls.bat
echo echo Copying required VIPS DLLs...>> release\scripts\copy-vips-dlls.bat
echo if not exist "bin" mkdir bin>> release\scripts\copy-vips-dlls.bat
echo.>> release\scripts\copy-vips-dlls.bat
echo echo Copying essential VIPS DLLs...>> release\scripts\copy-vips-dlls.bat
echo copy "C:\vips\bin\libvips-42.dll" "bin\" 2^>nul>> release\scripts\copy-vips-dlls.bat
echo copy "C:\vips\bin\libglib-2.0-0.dll" "bin\" 2^>nul>> release\scripts\copy-vips-dlls.bat
echo copy "C:\vips\bin\libgobject-2.0-0.dll" "bin\" 2^>nul>> release\scripts\copy-vips-dlls.bat
echo copy "C:\vips\bin\libffi-8.dll" "bin\" 2^>nul>> release\scripts\copy-vips-dlls.bat
echo copy "C:\vips\bin\libintl-8.dll" "bin\" 2^>nul>> release\scripts\copy-vips-dlls.bat
echo copy "C:\vips\bin\zlib1.dll" "bin\" 2^>nul>> release\scripts\copy-vips-dlls.bat
echo.>> release\scripts\copy-vips-dlls.bat
echo echo DLLs copied. You can now run ttc.exe from this directory.>> release\scripts\copy-vips-dlls.bat
echo echo.>> release\scripts\copy-vips-dlls.bat
echo echo For portable use, keep the bin folder with ttc.exe>> release\scripts\copy-vips-dlls.bat

echo Creating installation script...
echo @echo off> release\INSTALL.bat
echo echo Test Target Cropper (C Version) Installation>> release\INSTALL.bat
echo echo ========================================>> release\INSTALL.bat
echo echo.>> release\INSTALL.bat
echo echo 1. Copy VIPS DLLs (optional)>> release\INSTALL.bat
echo echo    scripts\copy-vips-dlls.bat>> release\INSTALL.bat
echo echo.>> release\INSTALL.bat
echo echo 2. Test the installation>> release\INSTALL.bat
echo echo    scripts\run-ttc-release.bat --help>> release\INSTALL.bat
echo echo.>> release\INSTALL.bat
echo echo 3. Ready to use!>> release\INSTALL.bat
echo echo.>> release\INSTALL.bat
echo echo See docs\README.md for usage instructions>> release\INSTALL.bat
echo pause>> release\INSTALL.bat

echo Creating release notes...
echo # Test Target Cropper v1.2.0 - C Version> release\RELEASE_NOTES.md
echo.>> release\RELEASE_NOTES.md
echo ## Release Information>> release\RELEASE_NOTES.md
echo - **Version:** 1.2.0>> release\RELEASE_NOTES.md
echo - **Date:** %date%>> release\RELEASE_NOTES.md
echo - **Language:** C (VIPS image processing)>> release\RELEASE_NOTES.md
echo.>> release\RELEASE_NOTES.md
echo ## What's New>> release\RELEASE_NOTES.md
echo - Complete rewrite from Python to C>> release\RELEASE_NOTES.md
echo - Much smaller executable (94KB vs Python runtime)>> release\RELEASE_NOTES.md
echo - Faster performance (native C)>> release\RELEASE_NOTES.md
echo - Cross-platform build system>> release\RELEASE_NOTES.md
echo - Self-contained distribution>> release\RELEASE_NOTES.md
echo.>> release\RELEASE_NOTES.md
echo ## System Requirements>> release\RELEASE_NOTES.md
echo - Windows 7+ (primary target)>> release\RELEASE_NOTES.md
echo - VIPS image processing library>> release\RELEASE_NOTES.md
echo - See docs\INSTALL_WINDOWS.md for setup>> release\RELEASE_NOTES.md
echo.>> release\RELEASE_NOTES.md
echo ## Known Limitations>> release\RELEASE_NOTES.md
echo - Some DNG files may not be compatible (see docs\DNG_COMPATIBILITY.md)>> release\RELEASE_NOTES.md
echo - PNG files have full support>> release\RELEASE_NOTES.md
echo.>> release\RELEASE_NOTES.md
echo ## Installation>> release\RELEASE_NOTES.md
echo 1. Run INSTALL.bat>> release\RELEASE_NOTES.md
echo 2. Follow the on-screen instructions>> release\RELEASE_NOTES.md
echo 3. Test with: ttc.exe --help>> release\RELEASE_NOTES.md

echo Creating package info...
echo Package: Test Target Cropper> release\PACKAGE_INFO.txt
echo Version: 1.2.0>> release\PACKAGE_INFO.txt
echo Language: C>> release\PACKAGE_INFO.txt
echo Executable: ttc.exe>> release\PACKAGE_INFO.txt
echo Size: ~94KB>> release\PACKAGE_INFO.txt
echo Dependencies: VIPS library>> release\PACKAGE_INFO.txt
echo Platforms: Windows, Linux, macOS>> release\PACKAGE_INFO.txt
echo Build Date: %date%>> release\PACKAGE_INFO.txt

echo.
echo ========================================
echo Release Package Created!
echo ========================================
echo.

echo Package contents:
dir /b release

echo.
echo Package size:
dir /s release | findstr "File(s)"

echo.
echo Files in release\bin:
dir /b release\bin

echo.
echo To install:
echo 1. Copy the release folder to desired location
echo 2. Run release\INSTALL.bat
echo 3. Follow the installation instructions

echo.
echo Release package ready for distribution!
pause
