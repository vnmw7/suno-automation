# Suno Automation - Docker Desktop Edition

## Prerequisites
- Docker Desktop installed (Windows/Mac/Linux)
  - Download from: https://www.docker.com/products/docker-desktop/
- Minimum 4GB RAM available for Docker
- 2GB+ disk space for images and data

## Quick Start

### Windows Users
1. **Install Docker Desktop** from the link above
2. **Start Docker Desktop** and wait for it to be ready
3. **Double-click** `start.bat`
4. **Edit .env files** if prompted (first time only)
5. **Access the app** at http://localhost:3000

### Mac/Linux Users
1. **Install Docker Desktop** from the link above
2. **Start Docker Desktop** and wait for it to be ready
3. **Make scripts executable** (first time only):
   ```bash
   chmod +x start.sh stop.sh
   ```
4. **Run** `./start.sh`
5. **Edit .env files** if prompted (first time only)
6. **Access the app** at http://localhost:3000

## Apple Silicon Build Workflow

- **Native arm64 image**: `docker buildx build --platform linux/arm64 --target macos --tag suno-backend:latest-arm64 --load ./backend`
- **amd64 image (Rosetta/emulation)**: `docker buildx build --platform linux/amd64 --tag suno-backend:latest-amd64 --load ./backend`
- **Run locally**: `docker run -p 8000:8000 --rm -it suno-backend:latest-arm64` (swap tag for the amd64 build when testing Intel compatibility)
- **Force manual Camoufox provisioning** (use when upstream `camoufox fetch` fails for arm64):
  1. Export `CAMOUFOX_VERSION` (example: `export CAMOUFOX_VERSION=135.0.1-beta.24`).
  2. Download the archive: `curl -sSL -o camoufox.zip "https://github.com/daijro/camoufox/releases/download/v${CAMOUFOX_VERSION}/camoufox-${CAMOUFOX_VERSION}-lin.arm64.zip"`.
  3. Verify integrity (replace with the release checksum): `sha256sum camoufox.zip`.
  4. Unzip and inspect locally if needed: `unzip -l camoufox.zip`.
  5. Move the zip into `backend/build/artifacts/camoufox/`.
  6. Build with manual source: `docker buildx build --platform linux/arm64 --target macos --tag suno-backend:manual-arm64 --build-arg CAMOUFOX_SOURCE=manual --load ./backend`.

## Stopping the Application

### Windows
Double-click `stop.bat`

### Mac/Linux
Run `./stop.sh`

## Data Storage Locations
All your data is stored locally in these folders:
- **Downloaded MP3 files**: `./songs/` folder
- **Browser session data**: `./camoufox_session_data/` folder
- **Application logs**: `./logs/` folder

These folders are created automatically and persist even after stopping Docker.

## First Time Setup

### 1. Environment Variables
The first time you run the application, it will create `.env` files from templates. You need to edit:

**backend/.env** - Add your API keys:
- Supabase URL and Key
- Database credentials
- OpenAI/Gemini API keys (if using AI features)

**frontend/.env** - Usually no changes needed unless using custom ports

### 2. Browser Download
On first run, Camoufox browser will be downloaded automatically (one-time process, ~100MB).

## Troubleshooting

### Docker Desktop Not Running
**Error**: "Docker is not running"
**Solution**: Start Docker Desktop and wait for it to fully initialize before running start script

### Port Already in Use
**Error**: "Port 3000/8000 already in use"
**Solution**:
1. Stop any other applications using these ports, OR
2. Edit `docker-compose.yml` to use different ports

### Browser Doesn't Work on Linux
Run this command before starting:
```bash
xhost +local:docker
```

### Low Performance
1. Open Docker Desktop settings
2. Increase memory allocation to 4GB or more
3. Restart Docker Desktop

### Container Fails to Start
Check logs with:
```bash
docker-compose logs backend
docker-compose logs frontend
```

## Advanced Commands

### View Real-time Logs
```bash
docker-compose logs -f
```

### Restart Services
```bash
docker-compose restart
```

### Update to Latest Version
```bash
git pull
docker-compose build --no-cache
docker-compose up -d
```

### Clean Everything (Reset)
```bash
docker-compose down -v
docker system prune -f
```
**Warning**: This removes all Docker data except your songs/logs folders

### Access Backend Shell
```bash
docker exec -it suno-backend /bin/bash
```

## Building from Source

If you make changes to the code, rebuild with:
```bash
docker-compose build
docker-compose up -d
```

## System Requirements

### Minimum
- OS: Windows 10/11, macOS 10.15+, Ubuntu 20.04+
- RAM: 4GB
- Storage: 2GB free space
- CPU: Dual-core processor

### Recommended
- RAM: 8GB or more
- Storage: 10GB free space
- CPU: Quad-core processor

## Features

- **Automated browser operations** with Camoufox
- **MP3 download and storage** in local folders
- **Web interface** at http://localhost:3000
- **API access** at http://localhost:8000
- **Persistent data** across restarts
- **No technical knowledge required** for basic usage

## Security Notes

- Application runs locally on your machine
- No data is sent to external servers (except API calls you configure)
- Keep your `.env` files secure (they contain your API keys)
- Downloaded files stay on your local machine

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs with `docker-compose logs`
3. Check project documentation in the main README

## Uninstallation

1. Stop the application (`stop.bat` or `./stop.sh`)
2. Remove containers: `docker-compose down -v`
3. Delete the application folder
4. Optionally, uninstall Docker Desktop
