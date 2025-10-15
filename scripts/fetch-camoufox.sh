#!/bin/bash
#
# Download the Camoufox archive required for arm64 backend builds.

set -o errexit
set -o nounset
set -o pipefail

strProjectRoot="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
strArtifactsDir="${strProjectRoot}/backend/build/artifacts/camoufox"

if ! command -v curl >/dev/null 2>&1; then
  echo "ERROR: curl is required to download Camoufox." >&2
  exit 1
fi

strVersion="${CAMOUFOX_VERSION:-}"
if [[ -z "$strVersion" ]]; then
  strVersion="$(grep -Eo 'ARG CAMOUFOX_VERSION=.+$' "${strProjectRoot}/backend/Dockerfile" | head -n1 | cut -d= -f2)"
fi

if [[ -z "$strVersion" ]]; then
  echo "ERROR: Unable to determine CAMOUFOX_VERSION." >&2
  exit 1
fi

mkdir -p "$strArtifactsDir"

strFilename="camoufox-${strVersion}-lin.arm64.zip"
strDestination="${strArtifactsDir}/${strFilename}"
strUrl="https://github.com/daijro/camoufox/releases/download/v${strVersion}/${strFilename}"

if [[ -f "$strDestination" ]]; then
  echo "Camoufox archive already present at $strDestination"
  exit 0
fi

echo "Downloading Camoufox ${strVersion} -> $strDestination"
curl -fL "$strUrl" -o "$strDestination"
echo "Download completed."
