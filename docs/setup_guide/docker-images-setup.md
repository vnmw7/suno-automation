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

Each service is published under a single architecture-neutral tag. Docker
automatically pulls the matching image for your platform:

- **Frontend development:** `suno-frontend:latest`
- **Backend API:** `suno-backend:latest`

When you cut formal releases, append semantic versions such as
`suno-frontend:1.2.3` and `suno-backend:1.2.3`.

## Build the Images with Helper Scripts

To remove platform-specific build commands, use the scripts in the project
`scripts/` folder. They detect your host architecture automatically and can also
publish multi-platform manifests when a registry is provided.

### Local build (host architecture)

```bash
# macOS/Linux
./scripts/build-images.sh --tag latest
```

```powershell
# Windows PowerShell
pwsh ./scripts/build-images.ps1 -Tag latest
```

The helper builds both frontend and backend and loads the images into Docker.
Use the optional flags to tailor the build:

- `--platform linux/amd64` – build for a specific platform (for example, debug amd64 issues on an Apple Silicon host).
- `--platform linux/amd64,linux/arm64 --push` – publish both platforms in one pass.
- `--manual-camoufox` – force the backend to consume a pre-downloaded Camoufox zip.
- `--fetch-camoufox` – download the Camoufox archive ahead of time without changing the source mode.

On Apple Silicon hosts the script still prepares the Camoufox archive automatically
for local builds so the backend works offline.

> **Manual Camoufox fallback:** The `--manual-camoufox` flag assumes the archive
> already exists under `backend/build/artifacts/camoufox/`. Fetch it with
> `./scripts/fetch-camoufox.sh` (or the PowerShell equivalent) when you need an
> offline build or an upstream download fails.

Verify the result:

```bash
docker images | grep suno-
```

### Publish a multi-platform manifest

Provide a registry (Docker Hub username, GHCR namespace, etc.) and pass `--push`
to build `linux/amd64` and `linux/arm64` images together:

```bash
./scripts/build-images.sh --registry your-namespace --tag latest --push
```

```powershell
pwsh ./scripts/build-images.ps1 -Registry your-namespace -Tag latest -Push
```

This workflow publishes a single tag (`your-namespace/suno-backend:latest`) whose
manifest lists both architectures. Developers only need `docker pull
your-namespace/suno-backend:latest`.

## Download Existing Images

When a teammate publishes images (for example, by running `./scripts/build-images.sh --registry <name> --push`), you can pull them by tag:

```bash
docker pull <registry-username>/suno-frontend:<tag>
docker pull <registry-username>/suno-backend:<tag>
```

For a single-click experience, use the bundled helper scripts in the `scripts/` directory:

- Windows: double-click `scripts/pull-images.bat` or run `scripts\pull-images.bat <registry> <tag>` from a terminal. The script prompts for missing values and pauses on completion.
- macOS/Linux: run `./scripts/pull-images.sh <registry> <tag>` (make it executable once with `chmod +x scripts/pull-images.sh`). The script accepts optional arguments and falls back to interactive prompts.

Common tag patterns:
- `latest` for the most recent stable build.
- Versioned tags such as `1.0.0` for reproducible deployments.

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
docker run --rm -it --name suno-frontend-preview -p 3001:3000 suno-frontend:latest

# Backend service
docker run --rm -it --name suno-backend-preview -p 8000:8000 suno-backend:latest
```

#### Troubleshooting mode (detailed logging)

If you need to keep the container running in the background while capturing
structured logs, use the detached flow below. The first line starts the container,
and the second line streams the startup logs with timestamps:

```bash
# Frontend (replace tag as needed)
docker run --rm -d --name suno-frontend-startup -p 3001:3000 suno-frontend:latest && \
docker logs suno-frontend-startup --follow --details --timestamps

# Backend service
docker run --rm -d --name suno-backend-startup -p 8000:8000 suno-backend:latest && \
docker logs suno-backend-startup --follow --details --timestamps
```

Stop the detached container later with `docker stop <container-name>` if you need to
tear it down manually.

### Integrate with docker-compose

For day-to-day development, `docker-compose` acts as the single entry point. The
project ships with a root `.env` file that Compose loads automatically:

```ini
TAG=latest
CAMOUFOX_SOURCE=auto
# FRONTEND_IMAGE=your-namespace/suno-frontend:latest
# BACKEND_IMAGE=your-namespace/suno-backend:latest
```

Leave the defaults as-is for local builds. To override any setting, copy the
file to `.env.local` (already ignored by Git), adjust the values, and pass it to
Compose:

```bash
docker-compose --env-file .env.local up --build -d
```

Running without an override continues to use `.env` automatically:

```bash
docker-compose up --build -d
```

This single command reads the configuration, rebuilds the images when needed,
and starts the stack in the background.

View log output and stop the stack when you are finished:

```bash
docker-compose logs -f
docker-compose down
```

### Local overrides

1. **Camoufox mode:** Set `CAMOUFOX_SOURCE=manual` inside `.env.local` when you
   want Compose to reuse a pre-downloaded archive.
2. **Remote images:** Uncomment and populate `FRONTEND_IMAGE` and
   `BACKEND_IMAGE` in `.env.local` to run published tags instead of building
   locally.
3. **Custom docker-compose overrides:** Create `docker-compose.override.yml`
   (already ignored by Git) for machine-specific tweaks such as bind mounts or
   debugging ports. Compose loads it automatically alongside the base file, so
   the primary workflow (`docker-compose up --build`) stays untouched.

When using remote images, `docker-compose up -d` is sufficient because Compose
skips the build step once an explicit image tag is provided.

## Share Images Offline

### Save to a Tarball

```bash
docker save suno-frontend:latest > suno-frontend.tar
docker save suno-backend:latest > suno-backend.tar
```

### Load from a Tarball

```bash
docker load < suno-frontend.tar
docker load < suno-backend.tar
```

## Troubleshooting

- **Buildx not found:** Run `docker buildx create --use` once, or upgrade Docker Desktop to a version that bundles Buildx.
- **Insufficient disk space:** Remove unused assets with `docker system prune --all`.
- **Camoufox download errors:** Use the manual build flow with `CAMOUFOX_SOURCE=manual` as shown above.
- **Permission denied on scripts (macOS):** Ensure executable permissions with `chmod +x scripts/*.sh`.
- **Multi-platform build is not supported:** Docker Desktop defaults to the lightweight `docker` builder, which cannot emulate other architectures. Create a multi-platform builder once and reuse it forever:
  ```bash
  docker buildx create --name multi-platform-builder --use
  docker buildx inspect --bootstrap
  ```
  After switching builders, rerun your original `buildx` command (for example,
  `pwsh ./scripts/build-images.ps1 -Registry your-namespace -Tag latest -Push`)
  and both `linux/amd64` and `linux/arm64` layers will be produced successfully.

## Container Hardening Best Practices

- **.dockerignore:** Keep `frontend/.dockerignore` and `backend/.dockerignore` updated to exclude `node_modules`, `.git`, temporary files, and local secrets. This reduces build context size and prevents accidental leakage.
- **Multi-stage builds:** Retain the existing multi-stage Dockerfiles so build tooling and dev dependencies never reach the final runtime image.
- **Non-root execution:** The backend Dockerfile already drops to the `suno-user` account. Apply the same pattern to any new services:
  ```dockerfile
  RUN addgroup --system suno-group && adduser --system --ingroup suno-group suno-user
  USER suno-user
  ```
  *Debian/Ubuntu note:* use `adduser --system --group suno-user` to achieve the same result.
- **Image scanning:** After publishing, run `docker scout cves <image>` or your registry's vulnerability scanner. Address high/critical issues before release.

## Next Steps

1. Push the images to a shared registry if they need to be consumed by other teammates.
2. Update deployment automation (for example, CI pipelines) to call the same build commands for reproducible images.
