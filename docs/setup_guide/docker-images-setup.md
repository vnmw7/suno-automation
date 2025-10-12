<!--
System: Suno Automation
Module: Docker Image Setup
File URL: docs/setup_guide/docker-images-setup.md
Purpose: Provide cross-platform steps to build, download, and run Suno Automation backend and frontend Docker images.
-->

# Docker Image Build and Usage Guide

This guide explains how to build, download, and run the Suno Automation frontend and backend Docker images on macOS and Windows hosts using the existing project scripts and Dockerfiles.

## Prerequisites

- Docker Desktop 4.31 or later (macOS or Windows) with the bundled Buildx plugin enabled.
- Git clone of the `suno-automation` repository.
- At least 4 GB of free RAM and 6 GB of disk space for image layers.
- Optional: Access to a Docker Hub (or compatible registry) account if you plan to push or pull shared images.

> **Tip:** Always start Docker Desktop before running any commands. The build scripts assume Docker is already running.

## Image Naming Conventions

- **Frontend macOS (arm64):** `suno-frontend:latest-macos-arm64`
- **Frontend Windows/Linux (amd64):** `suno-frontend:latest-windows-amd64`
- **Backend macOS (arm64):** `suno-backend:latest-macos-arm64`
- **Backend Windows/Linux (amd64):** `suno-backend:latest-windows-amd64`

You can adjust tags as needed. Use semantic tags (for example, `1.2.0`) when publishing images to a registry.

## Build the Frontend Image

### macOS (Apple Silicon arm64)

1. Open a terminal and change to the frontend directory:
   ```bash
   cd frontend
   ```
2. Make the script executable on the first run:
   ```bash
   chmod +x build-image-macos.sh
   ```
3. Build the arm64 image:
   ```bash
   ./build-image-macos.sh
   ```
   The script wraps the command below and loads the image into your local Docker Desktop installation:
   ```bash
   docker buildx build --platform linux/arm64 -f Dockerfile.macos -t suno-frontend:latest-macos-arm64 .
   ```
4. Verify the image:
   ```bash
   docker images suno-frontend
   ```

### Windows (amd64)

1. Launch a PowerShell window and change to the frontend folder:
   ```powershell
   Set-Location frontend
   ```
2. Run the build script:
   ```powershell
   .\build-image.bat
   ```
   The batch script invokes:
   ```powershell
   docker build -f Dockerfile.standalone -t suno-frontend:latest-windows-amd64 .
   ```
3. (Optional) Export the image to a tarball for offline sharing:
   ```powershell
   .\build-image.bat export
   ```
4. Confirm the image is available:
   ```powershell
   docker images suno-frontend
   ```

## Build the Backend Image

### macOS (Apple Silicon arm64)

1. From the project root, run:
   ```bash
   docker buildx build --platform linux/arm64 --target macos --tag suno-backend:latest-macos-arm64 --load ./backend
   ```
   This matches the workflow outlined in `README_DOCKER.md` and bundles the Camoufox browser for arm64.
2. (Optional) Provide a manually downloaded Camoufox archive if automated fetching fails:
   ```bash
   docker buildx build --platform linux/arm64 --target macos --tag suno-backend:manual-macos-arm64 --build-arg CAMOUFOX_SOURCE=manual --load ./backend
   ```
   Place the archive inside `backend/build/artifacts/camoufox/` before running the command.
3. Validate the resulting image:
   ```bash
   docker images suno-backend
   ```

### Windows (amd64)

1. Ensure Docker Desktop is configured for Linux containers (default).
2. Run the amd64 build:
   ```powershell
   docker buildx build --platform linux/amd64 --target macos --tag suno-backend:latest-windows-amd64 --load ./backend
   ```
   Buildx ships with Docker Desktop for Windows and provides consistent cross-platform output.
3. If Buildx is not available, fall back to the default builder:
   ```powershell
   docker build -t suno-backend:latest-windows-amd64 -f backend\Dockerfile backend
   ```
4. Confirm the image is available:
   ```powershell
   docker images suno-backend
   ```

## Download Existing Images

When a teammate publishes images (for example, via `frontend\docker-publish.bat`), you can pull them by tag:

```bash
docker pull <registry-username>/suno-frontend:<tag>
docker pull <registry-username>/suno-backend:<tag>
```

Common tag patterns:
- `latest-macos-arm64` or `latest-windows-amd64` for the most recent stable build.
- Versioned tags such as `1.0.0-macos-arm64` or `1.0.0-windows-amd64` for reproducible deployments.

Always confirm the pulled image:

```bash
docker images | grep suno
```

## Use the Images Locally

### Run Containers Directly

#### Quick start (recommended for demos)

These single commands start the container in the foreground and stream logs right
away, so non-technical teammates can copy and paste them without running an extra
`docker logs`. Use `Ctrl+C` when you are done—the container stops and is removed
automatically because of `--rm`.

```bash
# Frontend (replace tag as needed)
docker run --rm -it --name suno-frontend-preview -p 3001:3000 suno-frontend:latest-windows-amd64

# Backend arm64 (Mac host)
docker run --rm -it --name suno-backend-arm-preview -p 8000:8000 suno-backend:latest-macos-arm64

# Backend amd64 (Windows host)
docker run --rm -it --name suno-backend-amd-preview -p 8000:8000 suno-backend:latest-windows-amd64
```

#### Troubleshooting mode (detailed logging)

If you need to keep the container running in the background while capturing
structured logs, use the detached flow below. The first line starts the container,
and the second line streams the startup logs with timestamps:

```bash
# Frontend (replace tag as needed)
docker run --rm -d --name suno-frontend-startup -p 3001:3000 suno-frontend:latest-windows-amd64 && \
docker logs suno-frontend-startup --follow --details --timestamps

# Backend arm64 (Mac host)
docker run --rm -d --name suno-backend-arm-startup -p 8000:8000 suno-backend:latest-macos-arm64 && \
docker logs suno-backend-arm-startup --follow --details --timestamps

# Backend amd64 (Windows host)
docker run --rm -d --name suno-backend-amd-startup -p 8000:8000 suno-backend:latest-windows-amd64 && \
docker logs suno-backend-amd-startup --follow --details --timestamps
```

Stop the detached container later with `docker stop <container-name>` if you need to
tear it down manually.

### Integrate with docker-compose

Update `docker-compose.yml` (or a custom override) to point at the freshly built or downloaded tags:

```yaml
services:
  frontend:
    image: suno-frontend:latest-windows-amd64
  backend:
    image: suno-backend:latest-macos-arm64
```

Then restart the stack:

```bash
docker-compose down
docker-compose up -d
```

## Share Images Offline

### Save to a Tarball

```bash
docker save suno-frontend:latest-windows-amd64 > suno-frontend.tar
docker save suno-backend:latest-macos-arm64 > suno-backend-arm64.tar
```

### Load from a Tarball

```bash
docker load < suno-frontend.tar
docker load < suno-backend-arm64.tar
```

## Troubleshooting

- **Buildx not found:** Run `docker buildx create --use` once, or upgrade Docker Desktop to a version that bundles Buildx.
- **Insufficient disk space:** Remove unused assets with `docker system prune --all`.
- **Camoufox download errors:** Use the manual build flow with `CAMOUFOX_SOURCE=manual` as shown above.
- **Permission denied on scripts (macOS):** Ensure executable permissions with `chmod +x build-image-macos.sh`.

## Next Steps

1. Push the images to a shared registry if they need to be consumed by other teammates.
2. Update deployment automation (for example, CI pipelines) to call the same build commands for reproducible images.
