@echo off
setlocal enabledelayedexpansion
REM Final cleanup - keep only production build scripts

echo ========================================
echo Final Cleanup - Production Scripts Only
echo ========================================
echo.

echo Removing remaining alternative build scripts...
echo Keeping only: build-final-release.bat, build-w64devkit.bat, build.sh, build-success.bat
echo.

if exist "build-final.bat" (
    echo Removing build-final.bat
    del "build-final.bat"
)

if exist "build-success.bat" (
    echo Removing build-success.bat  
    del "build-success.bat"
)

echo.
echo Final cleanup complete!
echo.
echo Production build scripts that remain:
echo - build-final-release.bat (main production build)
echo - build-w64devkit.bat (w64devkit specific build)
echo - build.sh (Unix/Linux build)
echo.
echo Release scripts that remain:
echo - create-release.bat
echo - package-release.bat

pause
