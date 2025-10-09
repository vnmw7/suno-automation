#!/bin/bash

echo "Starting Suno Automation..."
echo

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running. Please start Docker first."
    exit 1
fi

# Check for .env files
if [ ! -f backend/.env ]; then
    echo "Creating backend .env from example..."
    cp backend/.env.example backend/.env
    echo "Please edit backend/.env with your configuration"
    read -p "Press enter to continue..."
fi

if [ ! -f frontend/.env ]; then
    echo "Creating frontend .env from example..."
    cp frontend/.env.example frontend/.env
    echo "Please edit frontend/.env with your configuration"
    read -p "Press enter to continue..."
fi

# For Linux, allow X11 forwarding
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xhost +local:docker 2>/dev/null || true
fi

# Start services
echo "Starting services..."
docker-compose up -d

if [ $? -eq 0 ]; then
    echo
    echo "Services started successfully!"
    echo
    echo "Frontend: http://localhost:3000"
    echo "Backend API: http://localhost:8000"
    echo
    echo "To view logs: docker-compose logs -f"
    echo "To stop: docker-compose down"
else
    echo "Failed to start services"
    exit 1
fi