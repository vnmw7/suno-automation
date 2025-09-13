# System: Suno Automation
# Module: Copy Camoufox Script
# Purpose: Copy Camoufox browser to distribution folder

$strCamoufoxPath = "$env:USERPROFILE\.camoufox"
$strDestPath = "dist\suno-automation-backend\.camoufox"

if (Test-Path $strCamoufoxPath) {
    Write-Host "Found Camoufox at: $strCamoufoxPath"
    Write-Host "Copying to distribution..."
    Copy-Item -Path $strCamoufoxPath -Destination $strDestPath -Recurse -Force
    Write-Host "Camoufox browser successfully copied to distribution!"
} else {
    Write-Host "Camoufox not found at: $strCamoufoxPath"
    Write-Host "Running camoufox fetch..."
    camoufox fetch
    if (Test-Path $strCamoufoxPath) {
        Write-Host "Now copying to distribution..."
        Copy-Item -Path $strCamoufoxPath -Destination $strDestPath -Recurse -Force
        Write-Host "Camoufox browser successfully copied!"
    } else {
        Write-Host "ERROR: Still cannot find Camoufox after fetch"
    }
}