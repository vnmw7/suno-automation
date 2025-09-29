@echo off
echo Stopping Frontend Docker Container...
docker-compose -f docker-compose.frontend.yml down
echo Frontend stopped.
pause