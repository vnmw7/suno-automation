@echo off
echo Building Suno Frontend Docker Image...
echo.

REM Set image name and tag
set IMAGE_NAME=suno-frontend
set IMAGE_TAG=latest
set FULL_IMAGE=%IMAGE_NAME%:%IMAGE_TAG%

echo Building Docker image: %FULL_IMAGE%
docker build -f Dockerfile.standalone -t %FULL_IMAGE% .

if %errorlevel% equ 0 (
    echo.
    echo Successfully built %FULL_IMAGE%
    echo.
    echo You can now:
    echo 1. Save to file: build-image.bat export
    echo 2. Push to registry: docker push %FULL_IMAGE%
    echo 3. Run locally: docker run -p 3001:3000 %FULL_IMAGE%
) else (
    echo Build failed!
    exit /b 1
)

REM Export image if requested
if "%1"=="export" (
    echo.
    echo Exporting image to suno-frontend.tar...
    docker save -o suno-frontend.tar %FULL_IMAGE%
    echo Image exported to suno-frontend.tar
    echo File size:
    powershell -Command "(Get-Item suno-frontend.tar).Length / 1MB" | findstr /r "[0-9]"
    echo MB
)

pause