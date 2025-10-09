# Suno Frontend Distribution Guide

## Distribution Methods

### Method 1: Docker Hub (Recommended for Public Distribution)

1. **Build and tag the image:**
```bash
cd frontend
docker build -f Dockerfile.standalone -t yourdockerhub/suno-frontend:v1.0.0 .
```

2. **Push to Docker Hub:**
```bash
docker login
docker push yourdockerhub/suno-frontend:v1.0.0
```

3. **Users can then install with:**
```bash
docker pull yourdockerhub/suno-frontend:v1.0.0
docker run -d -p 3001:3000 --name suno-frontend yourdockerhub/suno-frontend:v1.0.0
```

### Method 2: Portable Docker Image (Offline Distribution)

1. **Build the image:**
```bash
cd frontend
build-image.bat export
```

2. **This creates `suno-frontend.tar` file**

3. **Distribute the following files:**
   - `suno-frontend.tar` (Docker image)
   - `install-frontend.bat` (Installer script)
   - `.env.docker` (Configuration template)

4. **Users run:**
```bash
install-frontend.bat
```

### Method 3: GitHub Release Package

1. **Create a release package:**
```bash
cd frontend
mkdir suno-frontend-release
copy suno-frontend.tar suno-frontend-release\
copy install-frontend.bat suno-frontend-release\
copy .env.docker suno-frontend-release\.env.example
```

2. **Create ZIP archive:**
```bash
powershell Compress-Archive -Path suno-frontend-release\* -DestinationPath suno-frontend-v1.0.0.zip
```

3. **Upload to GitHub Releases**

### Method 4: Docker Compose Bundle

1. **Package structure:**
```
suno-frontend-bundle/
├── docker-compose.yml
├── Dockerfile.standalone
├── .env.example
├── install.bat
├── start.bat
├── stop.bat
└── README.md
```

2. **Users extract and run:**
```bash
install.bat
start.bat
```

## End User Requirements

### Prerequisites
- Docker Desktop installed
- Windows 10/11 (64-bit)
- 4GB RAM minimum
- Backend API running at `http://localhost:8000`

### Installation Steps for End Users

1. **Install Docker Desktop:**
   - Download from: https://www.docker.com/products/docker-desktop/
   - Run installer and restart computer

2. **Install Suno Frontend:**
   - Extract the distribution package
   - Run `install-frontend.bat`
   - Configure `.env` file with API credentials

3. **Start the Application:**
   - Run `start-suno-frontend.bat`
   - Open browser to `http://localhost:3001`

## Configuration

### Environment Variables
Create `.env` file with:
```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_KEY=your_supabase_key
VITE_API_URL=http://localhost:8000
```

## Distribution Checklist

- [ ] Build Docker image
- [ ] Test image locally
- [ ] Export image to tar file
- [ ] Create installer scripts
- [ ] Package configuration templates
- [ ] Create documentation
- [ ] Test on clean system
- [ ] Create release package
- [ ] Upload to distribution platform

## Support Files

### Minimal docker-compose.yml for distribution:
```yaml
version: '3.8'
services:
  frontend:
    image: suno-frontend:latest
    ports:
      - "3001:3000"
    environment:
      - NODE_ENV=production
    env_file:
      - .env
    restart: unless-stopped
```

## Troubleshooting Guide for End Users

### Common Issues:

1. **"Docker is not running"**
   - Start Docker Desktop
   - Wait for Docker to fully initialize

2. **"Port 3001 already in use"**
   - Stop other applications using the port
   - Or modify port in docker-compose.yml

3. **"Cannot connect to backend"**
   - Ensure backend is running at http://localhost:8000
   - Check firewall settings

4. **"Environment variables not set"**
   - Copy .env.example to .env
   - Fill in required API keys

## Version Management

Tag releases with semantic versioning:
- `v1.0.0` - Major release
- `v1.1.0` - Feature additions
- `v1.0.1` - Bug fixes

## License and Distribution Rights

Include appropriate license file with distribution package.