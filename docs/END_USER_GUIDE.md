# Suno Automation - Complete Installation Guide

## Quick Start (4 Steps)

### Step 1: Install Docker Desktop
Download and install Docker Desktop for your operating system:
- **Windows**: https://docs.docker.com/desktop/install/windows-install/
- **Mac**: https://docs.docker.com/desktop/install/mac-install/
- **Linux**: https://docs.docker.com/desktop/install/linux-install/

After installation, make sure Docker Desktop is running (you'll see the whale icon in your system tray).

### Step 2: Choose Backend Installation Method

**Option A: Docker Backend (Recommended)**
```bash
docker pull vnmw7/suno-backend:latest
docker run -d -p 8000:8000 --name suno-backend vnmw7/suno-backend:latest
```

**Option B: Manual Backend**
Download `suno-automation-backend.zip` from the releases page and extract it to a folder (e.g., `C:\suno-backend`), then double-click `suno-automation-backend.exe`.

### Step 3: Start the Frontend
Open Terminal (Mac/Linux) or Command Prompt (Windows) and run:

```bash
docker pull vnmw7/suno-frontend:latest
docker run -d -p 3001:3000 vnmw7/suno-frontend:latest
```

### Step 4: Access the Application
Open your web browser and go to: **http://localhost:3001**

---

## Prerequisites

Before installing, ensure you have:
- ✅ Docker Desktop installed and running
- ✅ At least 4GB of available RAM
- ✅ Active internet connection for initial download
- ✅ Either the backend package (`suno-automation-backend.zip`) OR willingness to use Docker backend

---

## Detailed Installation Instructions

### For Windows Users

1. **Start Docker Desktop**
   - Click the Docker Desktop icon
   - Wait for "Docker Desktop is running" message

2. **Open Command Prompt**
   - Press `Windows + R`
   - Type `cmd` and press Enter

3. **Install Backend and Frontend**

   **Option A: Docker Backend (Recommended)**
   ```cmd
   REM Install backend via Docker
   docker pull vnmw7/suno-backend:latest
   docker run -d -p 8000:8000 --name suno-backend --restart unless-stopped vnmw7/suno-backend:latest

   REM Install frontend
   docker pull vnmw7/suno-frontend:latest
   docker run -d -p 3001:3000 --restart unless-stopped vnmw7/suno-frontend:latest
   ```

   **Option B: Manual Backend**
   ```cmd
   REM Start manual backend
   cd C:\suno-backend
   start suno-automation-backend.exe

   REM Install frontend
   docker pull vnmw7/suno-frontend:latest
   docker run -d -p 3001:3000 --restart unless-stopped vnmw7/suno-frontend:latest
   ```

4. **Verify Installation**
   ```cmd
   docker ps
   ```
   You should see `suno-frontend` and optionally `suno-backend` in the list of running containers.

### For Mac/Linux Users

1. **Open Terminal**
   - Mac: Press `Cmd + Space`, type "Terminal"
   - Linux: Press `Ctrl + Alt + T`

2. **Install Backend and Frontend**

   **Option A: Docker Backend (Recommended)**
   ```bash
   # Install backend via Docker
   docker pull vnmw7/suno-backend:latest
   docker run -d -p 8000:8000 --name suno-backend --restart unless-stopped vnmw7/suno-backend:latest

   # Install frontend
   docker pull vnmw7/suno-frontend:latest
   docker run -d -p 3001:3000 --restart unless-stopped vnmw7/suno-frontend:latest
   ```

   **Option B: Manual Backend**
   ```bash
   # Install frontend only (backend must be running separately)
   docker pull vnmw7/suno-frontend:latest
   docker run -d -p 3001:3000 --restart unless-stopped vnmw7/suno-frontend:latest
   ```

3. **Access the Application**
   - Open your browser to: http://localhost:3001

---

## Configuration

### Using Custom Environment Variables

If you need to configure API endpoints or credentials:

1. **Create a configuration file** named `.env`:
   ```env
   VITE_SUPABASE_URL=your_supabase_url_here
   VITE_SUPABASE_KEY=your_supabase_key_here
   VITE_API_URL=http://localhost:8000
   ```

2. **Run with environment file**:
   ```bash
   docker run -d --name suno-frontend -p 3001:3000 --env-file .env vnmw7/suno-frontend:latest
   ```

---

## Daily Usage Commands

### Start the Frontend
```bash
docker start suno-frontend
```

### Stop the Frontend
```bash
docker stop suno-frontend
```

### Start the Backend (Docker only)
```bash
docker start suno-backend
```

### Stop the Backend (Docker only)
```bash
docker stop suno-backend
```

### View Logs
```bash
docker logs suno-frontend
docker logs suno-backend  # For Docker backend
```

### Restart the Frontend
```bash
docker restart suno-frontend
```

### Restart the Backend (Docker only)
```bash
docker restart suno-backend
```

### Check Status
```bash
docker ps | grep suno-frontend
docker ps | grep suno-backend  # For Docker backend
```

---

## Updating to Latest Version

To update to the newest version:

```bash
# Stop and remove current frontend
docker stop suno-frontend
docker rm suno-frontend

# Pull and run new frontend
docker pull vnmw7/suno-frontend:latest
docker run -d --name suno-frontend -p 3001:3000 --restart unless-stopped vnmw7/suno-frontend:latest

# Optional: Update Docker backend if using it
docker stop suno-backend
docker rm suno-backend
docker pull vnmw7/suno-backend:latest
docker run -d --name suno-backend -p 8000:8000 --restart unless-stopped vnmw7/suno-backend:latest
```

---

## Using Docker Compose (Alternative Method)

1. **Create `docker-compose.yml` file**:
   ```yaml
   version: '3.8'
   services:
     backend:
       image: vnmw7/suno-backend:latest
       container_name: suno-backend
       ports:
         - "8000:8000"
       restart: unless-stopped
       volumes:
         - ./songs:/app/songs
         - ./camoufox_session_data:/app/camoufox_session_data
         - ./logs:/app/logs

     frontend:
       image: vnmw7/suno-frontend:latest
       container_name: suno-frontend
       ports:
         - "3001:3000"
       restart: unless-stopped
       environment:
         - NODE_ENV=production
       depends_on:
         - backend
       extra_hosts:
         - "host.docker.internal:host-gateway"
   ```

2. **Start with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

3. **Stop with Docker Compose**:
   ```bash
   docker-compose down
   ```

4. **Frontend Only (if using manual backend)**:
   ```yaml
   version: '3.8'
   services:
     frontend:
       image: vnmw7/suno-frontend:latest
       container_name: suno-frontend
       ports:
         - "3001:3000"
       restart: unless-stopped
       environment:
         - NODE_ENV=production
       extra_hosts:
         - "host.docker.internal:host-gateway"
   ```

---

## Troubleshooting

### "Cannot connect to Docker daemon"
**Solution**: Make sure Docker Desktop is running. Look for the whale icon in your system tray.

### "Port 3001 is already in use"
**Solution**: Either stop the application using port 3001, or use a different port:
```bash
docker run -d --name suno-frontend -p 3002:3000 vnmw7/suno-frontend:latest
```
Then access at: http://localhost:3002

### "Container suno-frontend already exists"
**Solution**: Remove the existing container first:
```bash
docker rm -f suno-frontend
```

### "Cannot connect to backend API"
**Solution**:

**For Docker Backend:**
1. Ensure backend container is running: `docker ps | grep suno-backend`
2. Check backend logs: `docker logs suno-backend`
3. Restart backend if needed: `docker restart suno-backend`

**For Manual Backend:**
1. Ensure `suno-automation-backend.exe` is running
2. Check the console window shows "Server running at http://localhost:8000"
3. If the backend crashes, check Windows Defender/Antivirus settings
4. Make sure to keep the backend console window open while using the app

### "Page not loading at localhost:3001"
**Solution**:
1. Check if container is running: `docker ps`
2. Check logs for errors: `docker logs suno-frontend`
3. Try accessing: http://127.0.0.1:3001 instead

### "Permission denied" (Linux)
**Solution**: Run Docker commands with sudo:
```bash
sudo docker pull vnmw7/suno-frontend:latest
sudo docker run -d --name suno-frontend -p 3001:3000 vnmw7/suno-frontend:latest
```

---

## Uninstallation

To completely remove Suno Automation:

### 1. Stop and Remove Frontend:
```bash
# Stop and remove container
docker stop suno-frontend
docker rm suno-frontend

# Remove image
docker rmi vnmw7/suno-frontend:latest
```

### 2. Stop and Remove Backend (Docker):
```bash
# Stop and remove container
docker stop suno-backend
docker rm suno-backend

# Remove image
docker rmi vnmw7/suno-backend:latest
```

### 3. Stop Backend (Manual):
- Close the backend console window
- Delete the extracted backend folder

---

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 2GB free space
- **Docker**: Docker Desktop 4.0 or newer

### Recommended Requirements
- **RAM**: 8GB or more
- **CPU**: 2+ cores
- **Network**: Stable internet connection
- **Browser**: Chrome, Firefox, Safari, or Edge (latest versions)

---

## Security Notes

- The frontend runs locally on your machine
- No data is sent to external servers except configured API endpoints
- All connections to backend API are made from your local machine
- Ensure you trust the backend API endpoint before configuring

---

## Getting Help

### Check Application Status
```bash
docker logs suno-frontend --tail 50
```

### Version Information
```bash
docker inspect vnmw7/suno-frontend:latest | grep -i version
```

### Support Resources
- **GitHub Issues**: Report bugs or request features
- **Documentation**: Check the project repository
- **Docker Hub**: View image details at hub.docker.com

---

## Advanced Options

### Running with Custom Network
```bash
docker network create suno-network
docker run -d --name suno-frontend --network suno-network -p 3001:3000 vnmw7/suno-frontend:latest
```

### Resource Limits
```bash
docker run -d --name suno-frontend \
  -p 3001:3000 \
  --memory="1g" \
  --cpus="1" \
  vnmw7/suno-frontend:latest
```

### Auto-start on System Boot
The `--restart unless-stopped` flag ensures the container starts automatically when Docker starts.

---

## Quick Reference Card

| Action | Command |
|--------|---------|
| Install Frontend | `docker pull vnmw7/suno-frontend:latest` |
| Install Backend | `docker pull vnmw7/suno-backend:latest` |
| Run Frontend | `docker run -d --name suno-frontend -p 3001:3000 vnmw7/suno-frontend:latest` |
| Run Backend | `docker run -d --name suno-backend -p 8000:8000 vnmw7/suno-backend:latest` |
| Stop Frontend | `docker stop suno-frontend` |
| Stop Backend | `docker stop suno-backend` |
| Start Frontend | `docker start suno-frontend` |
| Start Backend | `docker start suno-backend` |
| Restart Frontend | `docker restart suno-frontend` |
| Restart Backend | `docker restart suno-backend` |
| View Frontend Logs | `docker logs suno-frontend` |
| View Backend Logs | `docker logs suno-backend` |
| Remove Frontend | `docker rm -f suno-frontend` |
| Remove Backend | `docker rm -f suno-backend` |
| Update Frontend | `docker pull vnmw7/suno-frontend:latest` |
| Update Backend | `docker pull vnmw7/suno-backend:latest` |
| Check Status | `docker ps \| grep suno-frontend` |
| Check Backend Status | `docker ps \| grep suno-backend` |

---

## Important Notes

### Backend Requirements
- A backend must be running for the application to work (either Docker or manual)
- For Docker backend: `docker start suno-backend`
- For manual backend: Keep `suno-automation-backend.exe` console window open
- If Windows Defender blocks the manual backend, you'll need to allow it in your security settings

### Data Storage
- Downloaded MP3 files are stored in the backend's local directory
- Browser session data is managed by the backend
- All processing happens locally on your machine