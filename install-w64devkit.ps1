# PowerShell script to install w64devkit
Write-Host "Installing w64devkit for Test Target Cropper..." -ForegroundColor Green

# Check if w64devkit already exists
if (Test-Path "w64devkit\bin\gcc.exe") {
    Write-Host "w64devkit already available!" -ForegroundColor Yellow
    & "w64devkit\bin\gcc.exe" --version
    
    Write-Host "`nBuilding ttc.exe..." -ForegroundColor Green
    & "w64devkit\bin\gcc.exe" -O2 -I"C:\vips\include" ttc.c -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Build successful! ttc.exe created." -ForegroundColor Green
        & "ttc.exe" --version
        & "ttc.exe" --help
    } else {
        Write-Host "Build failed!" -ForegroundColor Red
    }
    Read-Host "Press Enter to exit"
    exit
}

Write-Host "Downloading w64devkit..." -ForegroundColor Blue
try {
    Invoke-WebRequest -Uri "https://github.com/skeeto/w64devkit/releases/download/v1.2.0/w64devkit-v1.2.0.zip" -OutFile "w64devkit.zip" -UseBasicParsing
    Write-Host "Download successful!" -ForegroundColor Green
} catch {
    Write-Host "Download failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please download manually from: https://github.com/skeeto/w64devkit/releases" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Extracting w64devkit..." -ForegroundColor Blue
try {
    Expand-Archive -Path "w64devkit.zip" -DestinationPath "." -Force
    Write-Host "Extraction successful!" -ForegroundColor Green
} catch {
    Write-Host "Extraction failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please extract w64devkit.zip manually to w64devkit\ folder" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Clean up
Remove-Item "w64devkit.zip" -Force

Write-Host "Testing w64devkit installation..." -ForegroundColor Blue
if (Test-Path "w64devkit\bin\gcc.exe") {
    & "w64devkit\bin\gcc.exe" --version
    
    Write-Host "`nBuilding ttc.exe..." -ForegroundColor Green
    & "w64devkit\bin\gcc.exe" -O2 -I"C:\vips\include" ttc.c -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Build successful! ttc.exe created." -ForegroundColor Green
        & "ttc.exe" --version
        & "ttc.exe" --help
        Write-Host "`nInstallation complete!" -ForegroundColor Green
    } else {
        Write-Host "Build failed!" -ForegroundColor Red
        Write-Host "Checking VIPS installation..." -ForegroundColor Yellow
        
        if (Test-Path "C:\vips\include\vips\vips.h") {
            Write-Host "VIPS headers found" -ForegroundColor Green
        } else {
            Write-Host "ERROR: VIPS headers not found at C:\vips\include\vips\vips.h" -ForegroundColor Red
            Write-Host "Please run install-vips.bat first" -ForegroundColor Yellow
        }
        
        if (Test-Path "C:\vips\lib\vips.lib") {
            Write-Host "VIPS library found" -ForegroundColor Green
        } else {
            Write-Host "ERROR: VIPS library not found at C:\vips\lib\vips.lib" -ForegroundColor Red
            Write-Host "Please run install-vips.bat first" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "ERROR: w64devkit\bin\gcc.exe not found!" -ForegroundColor Red
}

Read-Host "Press Enter to exit"
