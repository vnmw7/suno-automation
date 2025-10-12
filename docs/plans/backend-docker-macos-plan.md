<!--
System: Suno Automation
Module: Backend Docker Compatibility
File URL: docs/plans/backend-docker-macos-plan.md
Purpose: Document the remediation plan to make backend Docker image reliable on macOS (Intel and Apple Silicon)
-->

# Backend Docker Compatibility Remediation Plan (macOS)

## Step 1 — Verify Camoufox Fetch Support Per Architecture
- **Objective**: determine whether upstream Camoufox binaries cover `linux/arm64` or only `linux/amd64`.
- **Actions**
  - Launch ephemeral `linux/arm64` container and run `python -m camoufox fetch --verbose`; record the download URL and outcome.
  - Repeat inside `linux/amd64` container for baseline comparison.
  - Save command outputs and observations to a new diagnostic note at `docs/backend/camoufox-arch-study.md`.
- **Outcome**: confirmed matrix that drives the rest of the plan (native support, emulation, or self-built artifacts).

## Step 2 — Patch `backend/Dockerfile` For Multi-Arch Operation
- **Current Snippets**
  ```Dockerfile
  FROM python:3.11-slim AS builder
  WORKDIR /app
  …
  COPY --from=builder /install /usr/local
  COPY . .
  …
  RUN python -c "from camoufox import fetch; fetch()" || true
  ```
- **Actions**
  - Introduce `ARG TARGETARCH` and map Docker´s architecture token to the fetcher’s expectations.
  - Install extra build tools (`build-essential`, `libffi-dev`, etc.) only on architectures that will fall back to alternative automation.
  - Add a dedicated `macos` build target (or companion `backend/Dockerfile.macos`) so CI can run `docker buildx build --target macos --platform linux/arm64 -t ${REGISTRY}/suno-backend:macos .` and publish a macOS-focused image separate from the multi-arch Linux build.
  - Convert the Dockerfile to a two-stage build (`builder` + runtime) that:
    - Uses `python:3.11-slim-bookworm` in both stages.
    - Installs `curl` and `unzip` only in the builder, pins `CAMOUFOX_VERSION`, and installs `camoufox[geoip]`.
    - Branches on `TARGETARCH`: manual `curl` download for `arm64`; retains `python -m camoufox fetch` for `amd64`.
    - Normalizes the binary location by symlinking to `/build/camoufox` before copying into the runtime image.
    - Creates a non-root `suno-user`, ensures `PATH` includes `/home/suno-user/.local/bin`, and copies only required artifacts to keep the runtime layer lean.
  - Replace unconditional `fetch()` with a guarded helper:
    - If `TARGETARCH` matches a supported Camoufox binary, download it.
    - Otherwise set `CAMOUFOX_DISABLED=1` (to activate a different anti-detection strategy) without failing the build.
  - Support manual Camoufox provisioning by honoring `CAMOUFOX_SOURCE=manual` and copying a pre-downloaded archive from `/build/artifacts/camoufox` into `/app/.cache/camoufox` when present.
  - Ensure browser cache directories remain in `/app/.cache` for persistence.

## Step 3 — Harden Runtime Browser Loader (Camoufox vs. Allowed Fallbacks)
- **Key Files**
  - `backend/lib/login.py`
  - `backend/utils/camoufox_actions.py`
- **Actions**
  - Introduce `backend/utils/browser_provider.py` that exposes a Result-pattern API returning either a Camoufox factory (when enabled) or the project-approved fallback (e.g., Camoufox-compatible builds or the team’s alternative stealth solution—*not* plain Playwright*).
  - Move top-level `Camoufox` imports behind this abstraction to avoid import-time crashes.
  - Update existing call sites to consume the Result and surface clear error messages.
  - Align variable names with the mandated prefixes (e.g., `blnUseCamoufox`, `strBrowserArch`).
  - Add focused unit tests under `backend/tests/` validating both success and graceful-degradation paths.

## Step 4 — Correct Compose Definitions And Expose Platform Overrides
- **Files**
  - `docker-compose.yml`
  - `backend/docker-compose.backend.yml`
- **Current Snippet**
  ```yaml
    backend:
      build:
        context: ./backend
        dockerfile: Dockerfile
      container_name: suno-backend
      restart: unless-stopped
  ```
- **Actions**
  - Fix `backend/docker-compose.backend.yml` build context to `.`.
  - Add `platform: ${BACKEND_PLATFORM:-linux/arm64}` (and similar for frontend if needed) so developers can switch between native arm and amd64 emulation without editing YAML.
  - Inject healthchecks for the backend service to fail fast when the browser layer misbehaves.
  - Ensure new environment flags (`CAMOUFOX_DISABLED`, architecture hints) propagate via `env_file`/`environment`.

## Step 5 — Document Apple Silicon Workflow And Camoufox Matrix
- **File**: `README_DOCKER.md`
- **Actions**
  - Add “Apple Silicon (M-series)” section covering:
    - Native `linux/arm64` build command (`docker compose build` with new platform overrides).
    - When and how to force `linux/amd64` emulation via `BACKEND_PLATFORM=linux/amd64`.
    - Reference to the verified Camoufox matrix (Step 1) and the fallback strategy activated when Camoufox is disabled.
    - Steps for manual Camoufox installation: export `CAMOUFOX_VERSION`, download the approved archive (`curl -sSL -o camoufox.zip "https://github.com/daijro/camoufox/releases/download/v${CAMOUFOX_VERSION}/camoufox-${CAMOUFOX_VERSION}-lin.arm64.zip"`), verify via `sha256sum`, unzip into `assets/browsers/camoufox`, `chmod +x` the binary, and set `CAMOUFOX_SOURCE=manual` before rebuilding.
    - Example build commands for each architecture (`docker buildx build --platform linux/arm64 --target macos --tag suno-backend:latest-arm64 --load ./backend` and `docker buildx build --platform linux/amd64 --tag suno-backend:latest-amd64 --load ./backend`) plus `docker run` snippets for validation.
  - Include recommended diagnostic commands (`docker buildx build`, `python -m camoufox fetch --verbose`).
  - Note memory/CPU requirements for emulation.

## Step 6 — Optional: Provide Controlled Arm64 Camoufox Build Procedure
- **Deliverable**: new doc at `docs/backend/camoufox-arm64-build.md`.
- **Content**
  - Reference official builder workflow:
    ```
    docker build -t camoufox-builder .
    docker run -v "$(pwd)/dist:/app/dist" camoufox-builder --target linux --arch arm64
    ```
  - Outline resource requirements (RAM, disk, build time) and caching tips.
  - Clarify that the produced artifact must be hosted in an internal registry and wired into Step 2 logic.

## Step 7 — Validation Checklist (To Execute Post-Implementation)
- Build and run backend images for both `linux/arm64` and `linux/amd64` via `docker buildx build`.
- Start containers with `.env` supplied; curl `/health` and record responses.
- Execute unit tests covering the browser provider result handling.
- Log all results in `docs/backend/camoufox-arch-study.md` for future regression tracking.

---

### Items Requiring Further Confirmation
1. Whether current upstream `python -m camoufox fetch` returns a `lin.arm64.zip` payload (Step 1 provides evidence).
2. Runtime stability of Camoufox on arm64 even when the binary is available (watch for Gecko/GTK regressions).
3. Specification of the approved anti-detection fallback. The plan assumes a stealth-capable alternative (not plain Playwright); confirm with stakeholders before coding.
