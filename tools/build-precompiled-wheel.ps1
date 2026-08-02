# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
#
# Build a precompiled wheel with the correct platform tag.
#
# Usage:
#   uv run powershell tools/build-precompiled-wheel.ps1
#
# This script:
#   1. Builds the wheel to a temp directory (avoids overwriting existing wheels)
#   2. Fixes the platform tag via fix-wheel-tag.py
#   3. Moves the fixed wheel to dist/

$ErrorActionPreference = "Stop"

$ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ROOT

# Use the system temp directory (cross-platform)
$BUILD_DIR = Join-Path ([System.IO.Path]::GetTempPath()) "tanga-build-$PID"
New-Item -ItemType Directory -Force -Path $BUILD_DIR | Out-Null

Write-Host "Building precompiled wheel..."
uv build --wheel -o $BUILD_DIR

Write-Host "Fixing wheel platform tag..."
uv run python tools/fix-wheel-tag.py -d $BUILD_DIR

Write-Host "Moving fixed wheel to dist/"
New-Item -ItemType Directory -Force -Path dist | Out-Null
Move-Item -Path "$BUILD_DIR/tanga_py-*.whl" -Destination dist/

Write-Host "Cleaning up temp build dir..."
Remove-Item -Recurse -Force $BUILD_DIR

Write-Host "Done. Wheels in dist/:"
Get-ChildItem dist/tanga_py-*.whl | ForEach-Object { Write-Host "  $($_.Name)" }