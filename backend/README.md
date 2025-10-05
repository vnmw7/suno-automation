# suno-automation

## Initialization

- Create a virtual python environment

    ```bash
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    ```

- Install python packages

    ```bash
    pip install -r requirements
    ```

## Docker (Standalone Backend)

The backend can run in isolation via Docker. Ensure Docker Desktop (or any modern Docker Engine) is installed and running.

1. Copy `.env.sample` to `.env` and populate the required secrets.
2. Build and start the container:

    ```bash
    docker compose -f backend/docker-compose.backend.yml up --build
    ```

3. The API becomes available at `http://localhost:8000`.

### Camoufox Runtime Notes

- The container pre-installs Camoufox and downloads the patched Firefox binary during build.
- Browser cache and session data persist locally through the mounted folders:
  - `./camoufox_session_data` stores profile data.
  - `./logs` retains backend logs.
  - `./songs` keeps downloaded audio assets.
- Subsequent runs reuse the cached browser assets located in the `camoufox-cache` volume.
