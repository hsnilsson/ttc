@echo off
echo Downloading w64devkit manually...
echo.

echo Please open this link in your browser:
echo https://github.com/skeeto/w64devkit/releases/latest
echo.
echo Download the file named: w64devkit-v1.2.0.zip
echo.
echo After downloading, extract it to this folder.
echo You should have a w64devkit\ folder with bin\gcc.exe inside.
echo.

echo Press any key to open the download page...
start https://github.com/skeeto/w64devkit/releases/latest
pause

echo.
echo Once you've extracted w64devkit, run: build-w64devkit.bat
echo.
