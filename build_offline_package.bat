@echo off
chcp 65001 >nul
echo ========================================
echo Build Offline Package
echo ========================================
echo.

if not exist "dist\PetReport\PetReport.exe" (
    echo dist\PetReport\ not found. Run build_exe_minimal.bat first.
    pause
    exit /b 1
)

set PKG=PetReport_Offline
if exist "%PKG%" rmdir /s /q "%PKG%"
mkdir "%PKG%"

echo [1/3] Copying app...
xcopy /E /I /Y "dist\PetReport\*" "%PKG%\" >nul

echo [2/3] Skipping vc_redist to keep package small. If target PC shows DLL error, download vc_redist.x64.exe from https://aka.ms/vs/17/release/vc_redist.x64.exe

echo [3/3] Creating instructions...
(
echo ========================================
echo PetReport - Offline Usage
echo ========================================
echo.
echo 1. Copy this entire folder to the target PC ^(USB / network^)
echo 2. If "api-ms-win-core-path-l1-1-0.dll" or similar error:
echo    - Run vc_redist.x64.exe in this folder first
echo    - Restart, then run PetReport.exe
echo 3. Run PetReport.exe
echo.
echo Note: PDF export needs Word or LibreOffice on target PC.
) > "%PKG%\README.txt"

echo.
echo Done. Output: %PKG%\
echo Copy this folder to the offline PC.
pause
