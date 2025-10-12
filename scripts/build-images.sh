#!/bin/bash
#
# Simplified multi-platform build helper for Suno Automation images.

set -o errexit
set -o nounset
set -o pipefail

fncUsage() {
  cat <<'EOF'
Usage: scripts/build-images.sh [--registry REGISTRY] [--tag TAG] [--push]
                               [--platform PLATFORMS] [--manual-camoufox]
                               [--fetch-camoufox]

Options:
  --registry REGISTRY  Optional registry or namespace prefix (e.g. myrepo).
  --tag TAG            Image tag to use (default: latest).
  --push               Build linux/amd64 and linux/arm64 images and push them.
                       Without --push the script builds only the local host
                       architecture and loads it into Docker for immediate use.
  --platform PLATFORMS Override the target platforms (comma separated). Example:
                       --platform linux/amd64 or --platform linux/amd64,linux/arm64
  --manual-camoufox    Use the pre-downloaded Camoufox archive instead of fetching
                       during the build (sets CAMOUFOX_SOURCE=manual).
  --fetch-camoufox     Download the Camoufox archive before building. Useful for
                       offline or cached builds. Implied when --manual-camoufox is set.
  -h, --help           Show this help message.

Environment:
  DOCKER_BUILDKIT      Set to 0 to disable BuildKit if required.
EOF
}

strRegistry=""
strTag="latest"
blnPush=false
strPlatformOverride=""
blnManualCamoufox=false
blnFetchCamoufox=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --registry)
      [[ $# -ge 2 ]] || { echo "ERROR: --registry requires a value" >&2; exit 1; }
      strRegistry="$2"
      shift 2
      ;;
    --tag)
      [[ $# -ge 2 ]] || { echo "ERROR: --tag requires a value" >&2; exit 1; }
      strTag="$2"
      shift 2
      ;;
    --push)
      blnPush=true
      shift
      ;;
    --platform)
      [[ $# -ge 2 ]] || { echo "ERROR: --platform requires a value" >&2; exit 1; }
      strPlatformOverride="$2"
      shift 2
      ;;
    --manual-camoufox)
      blnManualCamoufox=true
      blnFetchCamoufox=true
      shift
      ;;
    --fetch-camoufox)
      blnFetchCamoufox=true
      shift
      ;;
    -h|--help)
      fncUsage
      exit 0
      ;;
    *)
      echo "ERROR: Unknown option $1" >&2
      fncUsage
      exit 1
      ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is not installed or not in PATH." >&2
  exit 1
fi

if ! docker buildx version >/dev/null 2>&1; then
  echo "ERROR: docker buildx is required. Please enable Docker Desktop Buildx support." >&2
  exit 1
fi

strUname="$(uname -m)"
case "$strUname" in
  x86_64|amd64)
    strHostPlatform="linux/amd64"
    ;;
  arm64|aarch64)
    strHostPlatform="linux/arm64"
    ;;
  *)
    echo "ERROR: Unsupported host architecture: $strUname" >&2
    exit 1
    ;;
esac

if $blnPush; then
  strPlatforms="${strPlatformOverride:-linux/amd64,linux/arm64}"
  arrOutputFlag=(--push)
else
  strPlatforms="${strPlatformOverride:-$strHostPlatform}"
  arrOutputFlag=(--load)
fi

if [[ -n "$strRegistry" ]]; then
  strFrontendImage="${strRegistry}/suno-frontend:${strTag}"
  strBackendImage="${strRegistry}/suno-backend:${strTag}"
else
  strFrontendImage="suno-frontend:${strTag}"
  strBackendImage="suno-backend:${strTag}"
fi

echo "Building frontend image -> $strFrontendImage ($strPlatforms)"
docker buildx build \
  --file frontend/Dockerfile \
  --platform "$strPlatforms" \
  --tag "$strFrontendImage" \
  "${arrOutputFlag[@]}" \
  frontend

strCamoufoxSource="auto"
if $blnManualCamoufox; then
  strCamoufoxSource="manual"
fi

# Determine if we should fetch the Camoufox archive ahead of the backend build.
if [[ "$strPlatforms" == *"linux/arm64"* ]]; then
  if ! $blnManualCamoufox && ! $blnPush && [[ -z "$strPlatformOverride" && "$strHostPlatform" == "linux/arm64" ]]; then
    # Maintain the previous default behaviour for local Apple Silicon builds.
    blnFetchCamoufox=true
    strCamoufoxSource="manual"
  fi

  if $blnFetchCamoufox; then
    echo "Preparing Camoufox archive for arm64 build..."
    bash scripts/fetch-camoufox.sh
  fi
fi

arrBackendArgs=(
  --file backend/Dockerfile
  --platform "$strPlatforms"
  --tag "$strBackendImage"
  --build-arg "CAMOUFOX_SOURCE=$strCamoufoxSource"
)

echo "Building backend image -> $strBackendImage ($strPlatforms) [CAMOUFOX_SOURCE=$strCamoufoxSource]"
docker buildx build \
  "${arrBackendArgs[@]}" \
  "${arrOutputFlag[@]}" \
  backend

echo "Build complete."
