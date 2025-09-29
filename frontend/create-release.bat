@echo off
echo ========================================
echo Creating Suno Frontend Release Package
echo ========================================
echo.

REM Set version
set /p VERSION=Enter version number (e.g., 1.0.0):
set RELEASE_NAME=suno-frontend-v%VERSION%
set RELEASE_DIR=%RELEASE_NAME%

echo Creating release: %RELEASE_NAME%
echo.

REM Clean previous release
if exist %RELEASE_DIR% (
    echo Cleaning previous release directory...
    rmdir /s /q %RELEASE_DIR%
)

REM Create release directory
mkdir %RELEASE_DIR%

echo Building Docker image...
call build-image.bat export

if not exist suno-frontend.tar (
    echo ERROR: Failed to create Docker image export!
    pause
    exit /b 1
)

echo.
echo Copying files to release directory...

REM Copy required files
copy suno-frontend.tar %RELEASE_DIR%\
copy install-frontend.bat %RELEASE_DIR%\
copy .env.docker %RELEASE_DIR%\.env.example
copy docker-compose.frontend.yml %RELEASE_DIR%\docker-compose.yml

REM Create README for end users
echo # Suno Frontend - Installation Guide > %RELEASE_DIR%\README.txt
echo. >> %RELEASE_DIR%\README.txt
echo Version: %VERSION% >> %RELEASE_DIR%\README.txt
echo. >> %RELEASE_DIR%\README.txt
echo ## Prerequisites: >> %RELEASE_DIR%\README.txt
echo - Docker Desktop installed and running >> %RELEASE_DIR%\README.txt
echo - Backend API running at http://localhost:8000 >> %RELEASE_DIR%\README.txt
echo. >> %RELEASE_DIR%\README.txt
echo ## Installation: >> %RELEASE_DIR%\README.txt
echo 1. Run install-frontend.bat >> %RELEASE_DIR%\README.txt
echo 2. Edit .env file with your API credentials >> %RELEASE_DIR%\README.txt
echo 3. Run start-suno-frontend.bat >> %RELEASE_DIR%\README.txt
echo 4. Open http://localhost:3001 in your browser >> %RELEASE_DIR%\README.txt
echo. >> %RELEASE_DIR%\README.txt
echo ## Support: >> %RELEASE_DIR%\README.txt
echo For issues, visit: https://github.com/yourusername/suno-automation >> %RELEASE_DIR%\README.txt

REM Create version file
echo %VERSION% > %RELEASE_DIR%\version.txt

echo.
echo Creating ZIP archive...
powershell -Command "Compress-Archive -Path '%RELEASE_DIR%\*' -DestinationPath '%RELEASE_NAME%.zip' -Force"

if exist %RELEASE_NAME%.zip (
    echo.
    echo ========================================
    echo Release package created successfully!
    echo ========================================
    echo.
    echo Package: %RELEASE_NAME%.zip
    powershell -Command "$size = (Get-Item '%RELEASE_NAME%.zip').Length / 1MB; Write-Host 'Size:' $size.ToString('F2') 'MB'"
    echo.
    echo Contents:
    echo - Docker image (suno-frontend.tar)
    echo - Installer script (install-frontend.bat)
    echo - Configuration template (.env.example)
    echo - Docker Compose file
    echo - README.txt
    echo.
    echo You can now distribute %RELEASE_NAME%.zip to end users!
) else (
    echo ERROR: Failed to create ZIP archive!
)

REM Cleanup
echo.
set /p CLEANUP=Clean up temporary files? (y/n):
if /i "%CLEANUP%"=="y" (
    rmdir /s /q %RELEASE_DIR%
    del suno-frontend.tar
    echo Cleanup complete.
)

pause