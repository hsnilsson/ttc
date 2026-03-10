@echo off
REM Test for available C compilers

echo Checking for available C compilers...
echo.

echo 1. Testing for Visual Studio C++ (cl.exe):
where cl >nul 2>&1
if errorlevel 1 (
    echo   cl.exe not found in PATH
) else (
    echo   Found cl.exe:
    where cl
    echo   Version:
    cl 2>&1 | findstr "Version"
)

echo.
echo 2. Testing for MinGW gcc:
where gcc >nul 2>&1
if errorlevel 1 (
    echo   gcc not found in PATH
) else (
    echo   Found gcc:
    where gcc
    echo   Version:
    gcc --version | findstr "gcc"
)

echo.
echo 3. Testing for clang:
where clang >nul 2>&1
if errorlevel 1 (
    echo   clang not found in PATH
) else (
    echo   Found clang:
    where clang
    echo   Version:
    clang --version | findstr "clang"
)

echo.
echo 4. Checking common Visual Studio installations:
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" (
    echo   Found VS2022 Community
)
if exist "C:\Program Files\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat" (
    echo   Found VS2019 Community
)
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat" (
    echo   Found VS2019 Build Tools
)

echo.
echo 5. Checking for MinGW installations:
if exist "C:\mingw64\bin\gcc.exe" (
    echo   Found MinGW at C:\mingw64
)
if exist "C:\msys64\mingw64\bin\gcc.exe" (
    echo   Found MSYS2 MinGW at C:\msys64
)

echo.
echo If no compiler is found, you need to install one:
echo - Visual Studio Build Tools (free from Microsoft)
echo - MinGW-w64 (https://www.mingw-w64.org/)
echo - Or use WSL with gcc

pause
