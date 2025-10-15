#!/usr/bin/env pwsh
<#
.SYNOPSIS
Download the Camoufox archive required for arm64 backend builds.

.PARAMETER Version
Optional Camoufox version. When omitted, the script reads ARG CAMOUFOX_VERSION from backend/Dockerfile.
#>

[CmdletBinding()]
param(
    [string]$Version
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$strProjectRoot = Resolve-Path "$PSScriptRoot/.."
$strDockerfilePath = Join-Path $strProjectRoot "backend/Dockerfile"

if (-not $Version) {
    $strMatch = Select-String -Path $strDockerfilePath -Pattern 'ARG\s+CAMOUFOX_VERSION=(.+)' | Select-Object -First 1
    if (-not $strMatch) {
        throw "Unable to determine CAMOUFOX_VERSION from backend/Dockerfile."
    }
    $Version = $strMatch.Matches[0].Groups[1].Value
}

$strArtifactsDir = Join-Path $strProjectRoot "backend/build/artifacts/camoufox"
if (-not (Test-Path $strArtifactsDir)) {
    New-Item -ItemType Directory -Path $strArtifactsDir | Out-Null
}

$strFilename = "camoufox-$Version-lin.arm64.zip"
$strDestination = Join-Path $strArtifactsDir $strFilename
$strUrl = "https://github.com/daijro/camoufox/releases/download/v$Version/$strFilename"

if (Test-Path $strDestination) {
    Write-Host "Camoufox archive already present at $strDestination"
    exit 0
}

Write-Host "Downloading Camoufox $Version -> $strDestination"
Invoke-WebRequest -Uri $strUrl -OutFile $strDestination -UseBasicParsing
Write-Host "Download completed."
