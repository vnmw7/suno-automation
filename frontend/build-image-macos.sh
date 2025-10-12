#!/bin/bash
# System: Suno Automation
# Module: Frontend Docker Build Script for MacOS
# File URL: frontend/build-image-macos.sh
# Purpose: Script to build the ARM64 Docker image for MacOS users with Apple Silicon

echo "Building Suno Frontend Docker Image for MacOS (arm64)..."
set -e

IMAGE_NAME="suno-frontend-macos"
IMAGE_TAG="latest"
FULL_IMAGE="$IMAGE_NAME:$IMAGE_TAG"

echo "Building Docker image: $FULL_IMAGE"
docker buildx build --platform linux/arm64 -f Dockerfile.macos -t $FULL_IMAGE .

echo "Successfully built $FULL_IMAGE"