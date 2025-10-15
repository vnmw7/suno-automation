# Container Startup Remediation Plan

## Objectives
- Restore local accessibility of the backend at `http://localhost:8000` and the frontend at `http://localhost:3001`.
- Remove brittle behaviours in the current container start-up flow while honouring the Minimum Viable Approach.
- Reduce leakage of sensitive configuration from the launcher script and align runtime configuration with framework expectations.

## Proposed Changes

### scripts/start-containers.bat
**Current snippet**
```bat
set "BASE_DIR=%~dp0.."
...
set "BACKEND_CMD=!BACKEND_CMD! -v !BASE_DIR!\logs:/app/logs"
set "BACKEND_CMD=!BACKEND_CMD! -v !BASE_DIR!\songs:/app/songs"
set "BACKEND_CMD=!BACKEND_CMD! -v !BASE_DIR!\camoufox_session_data:/app/camoufox_session_data"
...
set "FRONTEND_CMD=!FRONTEND_CMD! -p 3001:3000"
set "FRONTEND_CMD=!FRONTEND_CMD! !FRONTEND_ENV_VARS!"
set "FRONTEND_CMD=!FRONTEND_CMD! !FRONTEND_ENV_FILE!"
```

**Planned updates**
- Resolve `BASE_DIR` to an absolute path (`for %%I in ("%~dp0..") do set "BASE_DIR=%%~fI"`) and wrap all bind mounts in quotes (or switch to `--mount`) to avoid Windows path resolution failures.
- Keep zero-config defaults for end users by retaining inline fallback values, but allow overrides via existing environment variables and optional `.env` files; log a warning (not a hard failure) when secrets fall back to bundled defaults so rotated keys can be supplied later without blocking usage.
- Fail fast on `docker run` errors by capturing exit codes and streaming the last 50 log lines before exiting; remove the generic `pause` paths.
- After each container starts, poll `docker inspect --format "{{.State.Health.Status}}"` until it reports `healthy` (or a sensible retry limit is hit) before printing the success banner; on failure, surface the health JSON and recent logs.
- Keep the frontend port mapping at `-p 3001:3000` (Remix server exposes 3000) and add a final status table that includes both `.State.Status` and `.State.Health.Status`.
- Mask sensitive environment values in console output and log files while still surfacing which configuration source (inline default vs override) was used.

**Validation**
- `docker inspect --format "{{.Name}}\t{{.State.Status}}\t{{if .State.Health}}{{.State.Health.Status}}{{end}}" suno-backend-startup`.
- `curl http://localhost:8000/` and `curl http://localhost:3001/` after the health checks succeed.

### frontend/Dockerfile
**Current snippet**
```dockerfile
COPY --from=builder /app/build ./build
COPY --from=builder /app/public ./public
...
EXPOSE 3000
...
CMD ["npm", "start"]
```

**Planned updates**
- Keep the multi-stage build but tailor the runtime stage for Remix: copy the build output plus server assets into a final `node:20-alpine` image, set `HOST=0.0.0.0` and `PORT=3000`, and launch with `["npx","remix-serve","build/server/index.js"]`.
- Install a lightweight HTTP client (e.g., `apk add --no-cache curl`) so the container’s `HEALTHCHECK` can probe `http://127.0.0.1:3000/health` (add a small Remix route if needed) and surface readiness accurately.
- Ensure production dependencies only: re-use the `deps` stage for `npm ci --omit=dev`, copy the `build` artefacts and `package.json`, and avoid shipping the entire source tree.
- Document how runtime environment variables (Supabase keys, API URL, etc.) are injected by the launcher at container start so no rebuild is required for configuration changes.

**Validation**
- `docker build -t suno-frontend:test frontend`.
- `docker run --rm -p 3001:3000 suno-frontend:test && curl http://localhost:3001/health`.

### backend/Dockerfile
**Current snippet**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import http.client, sys; conn=http.client.HTTPConnection('127.0.0.1', 8000, timeout=5); conn.request('GET', '/'); status = conn.getresponse().status; sys.exit(0 if 200 <= status < 500 else 1)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Planned updates**
- Adjust the `CMD` to `["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]` to avoid PATH lookup issues across Python distributions.
- Keep the existing health check but parameterise the timeout via `ENV BACKEND_HEALTH_TIMEOUT=5` and read it within the probe command so the launcher can tune readiness delays without editing the Dockerfile.
- Add a simple `/health` FastAPI endpoint (backed by a lightweight dependency check) and point the health probe to it for clearer status reporting.
- Include comment guidance clarifying that configuration is injected via runtime environment variables supplied by the launcher (with inline defaults available for out-of-the-box usage).

**Validation**
- `docker build -t suno-backend:test backend`.
- `docker run --rm -p 18000:8000 suno-backend:test && curl http://localhost:18000/`.

### New runtime considerations
- Add a lightweight Remix `/health` route that returns a 200 response once server dependencies are ready; the Docker health check and launcher script will rely on this endpoint.
- Review logging in the launcher and containers to ensure sensitive configuration values are not echoed; redact or omit secrets from stdout/stderr where practical while retaining operational insight.

## Verification Plan
- Rebuild images locally (`docker build` for backend and frontend) and tag them for the launcher script.
- Run the updated `scripts/start-containers.bat` and confirm both health checks pass without manual intervention.
- Tail the generated log file in `logs/` to ensure sensitive values are not written in plain text.

## Security & Follow-Up
- Rotate the leaked Supabase and Google API credentials immediately; update inline defaults and any external stores accordingly.
- After successful validation, document the revised workflow in `README_DOCKER.md` and deprecate the old inline-secret workflow.
