#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
#
# Build a precompiled wheel with the correct platform tag.
#
# Usage:
#   uv run bash tools/build-precompiled-wheel.sh
#
# This script:
#   1. Builds the wheel to a temp directory (avoids overwriting existing wheels)
#   2. Fixes the platform tag via fix-wheel-tag.py
#   3. Moves the fixed wheel to dist/

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Use the system temp directory (cross-platform)
TMPDIR="$(python -c "from tempfile import gettempdir; print(gettempdir())")"
BUILD_DIR="$TMPDIR/tanga-build-$$"
mkdir -p "$BUILD_DIR"

echo "Building precompiled wheel..."
uv build --wheel -o "$BUILD_DIR"

echo "Fixing wheel platform tag..."
uv run python tools/fix-wheel-tag.py -d "$BUILD_DIR"

echo "Moving fixed wheel to dist/"
mkdir -p dist
mv "$BUILD_DIR"/tanga_py-*.whl dist/

echo "Cleaning up temp build dir..."
rm -rf "$BUILD_DIR"

echo "Done. Wheels in dist/:"
ls -1 dist/tanga_py-*.whl 2>/dev/null || true