@echo off
setlocal enabledelayedexpansion
REM Runtime script for ttc.exe with proper PATH setup

echo ========================================
echo Test Target Cropper (C Version) Runner
echo ========================================
echo.

REM Set up PATH for VIPS DLLs
set PATH=C:\vips\bin;!PATH!

echo Environment configured for VIPS
echo.

REM Pass all arguments to ttc.exe
ttc.exe %*

echo.
echo ========================================
echo Process Complete
echo ========================================

pause
