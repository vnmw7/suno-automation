#!/usr/bin/env pwsh
<#
.SYNOPSIS
Build Suno Automation Docker images for the local architecture or push multi-platform manifests.

.PARAMETER Registry
Optional registry or namespace (e.g. myrepo). When omitted, images are tagged locally.

.PARAMETER Tag
Image tag to apply. Defaults to latest.

.PARAMETER Push
When set, build linux/amd64 and linux/arm64 images and push them. Otherwise only the
host architecture is built and loaded into Docker.

.PARAMETER Platform
Override the target platform(s). Accepts a single platform (e.g. linux/amd64) or a
comma-separated list.

.PARAMETER ManualCamoufox
Use the pre-downloaded Camoufox archive instead of fetching during the build.

.PARAMETER FetchCamoufox
Download the Camoufox archive before building. Implied when ManualCamoufox is set.

.NOTES
When running on an Arm64 host without --Push the script automatically prepares the
manual archive so local builds continue to work offline.
#>

[CmdletBinding()]
param(
    [string]$Registry = "",
    [string]$Tag = "latest",
    [switch]$Push,
    [string]$Platform,
    [switch]$ManualCamoufox,
    [switch]$FetchCamoufox
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "docker is not installed or not in PATH."
}

try {
    docker buildx version | Out-Null
} catch {
    throw "docker buildx is required. Please enable Buildx support in Docker Desktop."
}

$strHostArch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture
switch ($strHostArch) {
    'X64'   { $strHostPlatform = 'linux/amd64' }
    'Arm64' { $strHostPlatform = 'linux/arm64' }
    default { throw "Unsupported host architecture: $strHostArch" }
}

if ($Push.IsPresent) {
    $strPlatforms = if ($Platform) { $Platform } else { 'linux/amd64,linux/arm64' }
    $arrOutput = @('--push')
} else {
    $strPlatforms = if ($Platform) { $Platform } else { $strHostPlatform }
    $arrOutput = @('--load')
}

if ([string]::IsNullOrWhiteSpace($Registry)) {
    $strFrontendImage = "suno-frontend:$Tag"
    $strBackendImage = "suno-backend-startup:$Tag"
} else {
    $strFrontendImage = "$Registry/suno-frontend:$Tag"
    $strBackendImage = "$Registry/suno-backend-startup:$Tag"
}

Write-Host "Building frontend image -> $strFrontendImage ($strPlatforms)"
$arrFrontendArgs = @(
    "buildx", "build",
    "--file", "frontend/Dockerfile",
    "--platform", $strPlatforms,
    "--tag", $strFrontendImage
) + $arrOutput + @("frontend")

& docker @arrFrontendArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$strCamoufoxSource = if ($ManualCamoufox.IsPresent) { "manual" } else { "auto" }
$blnFetchCamoufox = $FetchCamoufox.IsPresent -or $ManualCamoufox.IsPresent
$requiresArm64 = $strPlatforms -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ -eq 'linux/arm64' } | Measure-Object | Select-Object -ExpandProperty Count

if ($requiresArm64 -gt 0) {
    if (-not $ManualCamoufox.IsPresent -and -not $Push.IsPresent -and -not $Platform -and $strHostPlatform -eq 'linux/arm64') {
        $blnFetchCamoufox = $true
        $strCamoufoxSource = "manual"
    }

    if ($blnFetchCamoufox) {
        Write-Host "Preparing Camoufox archive for arm64 build..."
        & "$PSScriptRoot/fetch-camoufox.ps1"
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
}

Write-Host "Building backend image -> $strBackendImage ($strPlatforms) [CAMOUFOX_SOURCE=$strCamoufoxSource]"
$arrBackendArgs = @(
    "buildx", "build",
    "--file", "backend/Dockerfile",
    "--platform", $strPlatforms,
    "--tag", $strBackendImage,
    "--build-arg", "CAMOUFOX_SOURCE=$strCamoufoxSource"
) + $arrOutput + @("backend")

& docker @arrBackendArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Build complete."
