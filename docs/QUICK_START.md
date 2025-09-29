# 🚀 Suno Automation - Quick Start Guide

## Complete Setup in 2 Minutes

### Prerequisites
- ✅ [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- ✅ Backend package downloaded (`suno-automation-backend.zip`)

## Step 1: Setup Backend (Required)

### Download and Run Backend

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
| **Restart** the frontend | `docker restart suno-frontend` |
| **Update** to latest version | `docker pull vnmw7/suno-frontend:latest` |
| **Check** if it's running | `docker ps \| grep suno-frontend` |
| **View** logs/errors | `docker logs suno-frontend` |
| **Remove** completely | `docker rm -f suno-frontend` |

---

## First Time Setup Checklist

1. ☐ **Download Backend Package**
   - Download `suno-automation-backend.zip` from releases
   - Extract to a folder (e.g., `C:\suno-backend`)

2. ☐ **Install Docker Desktop**
   - Download from [docker.com](https://www.docker.com/products/docker-desktop/)
   - Run installer and restart computer

3. ☐ **Start Docker Desktop**
   - Look for the whale icon in system tray
   - Wait for "Docker Desktop is running"

4. ☐ **Start Backend**
   - Navigate to extracted backend folder
   - Double-click `suno-automation-backend.exe`
   - Keep the console window open

5. ☐ **Install Frontend**
   ```bash
   docker pull vnmw7/suno-frontend:latest
   docker run -d -p 3001:3000 vnmw7/suno-frontend:latest
   ```

6. ☐ **Open Browser**
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
→ Check Windows Defender/Antivirus - may need to allow `suno-automation-backend.exe`

**❌ Need to reset everything?**
```bash
docker rm -f suno-frontend
docker rmi vnmw7/suno-frontend:latest
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
```
C:\suno-backend\              # Backend folder
├── suno-automation-backend.exe  # Backend server
└── .env                          # Configuration file

Docker Container              # Frontend
└── vnmw7/suno-frontend:latest   # Running on port 3001
```

---

**Need the full guide?** See [END_USER_GUIDE.md](END_USER_GUIDE.md)