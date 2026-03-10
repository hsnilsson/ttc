@echo off
REM Run ttc.exe with proper VIPS library path (works from bash)

set PATH=C:\vips\bin;%PATH%

ttc.exe %*
