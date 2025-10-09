# 🚀 Suno Automation - Quick Start Guide

## Complete Setup in 2 Minutes

### Prerequisites
- ✅ [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- ✅ Either backend package downloaded (`suno-automation-backend.zip`) OR willingness to use Docker backend

## Step 1: Setup Backend (Required)

### Choose Backend Installation Method

**Option A: Docker Backend (Recommended)**
```bash
docker pull vnmw7/suno-backend:latest
docker run -d -p 8000:8000 --name suno-backend vnmw7/suno-backend:latest
```

**Option B: Manual Backend**
1. **Download the backend package:**
   - Download `suno-automation-backend.zip` from the releases page

2. **Extract and run:**
   - Extract the ZIP file to a folder (e.g., `C:\suno-backend`)
   - Double-click `suno-automation-backend.exe` to start the backend
   - The backend will run at http://localhost:8000
   - Keep this window open while using the application

## Step 2: Setup Frontend

### Installation

**Windows (Command Prompt):**
```cmd
docker pull vnmw7/suno-frontend:latest
docker run -d -p 3001:3000 vnmw7/suno-frontend:latest
start http://localhost:3001
```

**Mac/Linux (Terminal):**
```bash
docker pull vnmw7/suno-frontend:latest
docker run -d -p 3001:3000 vnmw7/suno-frontend:latest
open http://localhost:3001  # Mac
xdg-open http://localhost:3001  # Linux
```

✅ **That's it!** The complete application is now running at http://localhost:3001

---

## Essential Commands

| What you want to do | Command |
|-------------------|---------|
| **Start** the frontend | `docker start suno-frontend` |
| **Stop** the frontend | `docker stop suno-frontend` |
| **Start** the backend (Docker) | `docker start suno-backend` |
| **Stop** the backend (Docker) | `docker stop suno-backend` |
| **Restart** the frontend | `docker restart suno-frontend` |
| **Restart** the backend (Docker) | `docker restart suno-backend` |
| **Update** frontend to latest | `docker pull vnmw7/suno-frontend:latest` |
| **Update** backend to latest | `docker pull vnmw7/suno-backend:latest` |
| **Check** frontend status | `docker ps \| grep suno-frontend` |
| **Check** backend status | `docker ps \| grep suno-backend` |
| **View** frontend logs | `docker logs suno-frontend` |
| **View** backend logs | `docker logs suno-backend` |
| **Remove** frontend completely | `docker rm -f suno-frontend` |
| **Remove** backend completely | `docker rm -f suno-backend` |

---

## First Time Setup Checklist

1. ☐ **Install Docker Desktop**
   - Download from [docker.com](https://www.docker.com/products/docker-desktop/)
   - Run installer and restart computer

2. ☐ **Start Docker Desktop**
   - Look for the whale icon in system tray
   - Wait for "Docker Desktop is running"

3. ☐ **Setup Backend**

   **Option A: Docker Backend (Recommended)**
   ```bash
   docker pull vnmw7/suno-backend:latest
   docker run -d -p 8000:8000 --name suno-backend vnmw7/suno-backend:latest
   ```

   **Option B: Manual Backend**
   - Download `suno-automation-backend.zip` from releases
   - Extract to a folder (e.g., `C:\suno-backend`)
   - Double-click `suno-automation-backend.exe`
   - Keep the console window open

4. ☐ **Install Frontend**
   ```bash
   docker pull vnmw7/suno-frontend:latest
   docker run -d -p 3001:3000 vnmw7/suno-frontend:latest
   ```

5. ☐ **Open Browser**
   - Navigate to: http://localhost:3001
   - Bookmark for easy access

---

## Troubleshooting in 10 Seconds

**❌ "Docker command not found"**
→ Install Docker Desktop first

**❌ "Port 3001 already in use"**
→ `docker rm -f suno-frontend` then reinstall

**❌ "Cannot connect to Docker daemon"**
→ Start Docker Desktop application

**❌ "Page won't load"**
→ Check: `docker logs suno-frontend`

**❌ Backend not starting?**

**Docker Backend:**
→ Check: `docker logs suno-backend`
→ Restart: `docker restart suno-backend`

**Manual Backend:**
→ Check Windows Defender/Antivirus - may need to allow `suno-automation-backend.exe`

**❌ Need to reset everything?**
```bash
docker rm -f suno-frontend
docker rm -f suno-backend
docker rmi vnmw7/suno-frontend:latest
docker rmi vnmw7/suno-backend:latest
# Then reinstall from the top
```

---

## Pro Tips 💡

### Auto-start on Computer Boot
Add `--restart always` to your run command:
```bash
docker run -d -p 3001:3000 --restart always vnmw7/suno-frontend:latest
```

### Run Backend as Windows Service
Create a batch file to start backend automatically on Windows startup

### Use a Different Port
Change `-p 3001:3000` to `-p 8080:3000` to use port 8080 instead

### Save Resources When Not Using
```bash
docker stop suno-frontend  # Stop when not needed
docker start suno-frontend  # Start when needed again
```

---

### Complete Application Structure

**Docker Backend (Recommended):**
```
Docker Container              # Backend
└── vnmw7/suno-backend:latest   # Running on port 8000

Docker Container              # Frontend
└── vnmw7/suno-frontend:latest   # Running on port 3001
```

**Manual Backend:**
```
C:\suno-backend\              # Backend folder
├── suno-automation-backend.exe  # Backend server
└── .env                          # Configuration file

Docker Container              # Frontend
└── vnmw7/suno-frontend:latest   # Running on port 3001
```

---

**Need the full guide?** See [END_USER_GUIDE.md](END_USER_GUIDE.md)