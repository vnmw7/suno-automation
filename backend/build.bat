@echo off
REM System: Suno Automation
REM Module: Build Script
REM Purpose: Build standalone executable with PyInstaller and Camoufox

echo Building Suno Automation Backend...
echo.

REM Install PyInstaller if not installed
echo Installing PyInstaller...
pip install pyinstaller

REM Install Camoufox with geoip support
echo Installing Camoufox with dependencies...
pip install camoufox[geoip]

REM Install other requirements
echo Installing backend requirements...
pip install -r requirements.txt

REM Fetch Camoufox browser
echo Fetching Camoufox browser...
camoufox fetch

REM Clean previous builds
echo Cleaning previous builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM Build with PyInstaller
echo Building executable...
pyinstaller main.spec --clean

REM Copy Camoufox browser to dist - REQUIRED for standalone distribution
echo Copying Camoufox browser data to distribution...
if exist "%USERPROFILE%\.camoufox" (
    echo Found Camoufox browser, copying to distribution...
    xcopy /E /I /Y "%USERPROFILE%\.camoufox" "dist\suno-automation-backend\.camoufox"
    echo Camoufox browser successfully bundled!
) else (
    echo WARNING: Camoufox browser not found at %USERPROFILE%\.camoufox
    echo Users will need internet on first run to download the browser
)

echo.
echo Build complete! The executable is in: dist\suno-automation-backend\
echo.
echo To run the application:
echo   cd dist\suno-automation-backend
echo   suno-automation-backend.exe
echo.
pause