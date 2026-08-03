#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

r"""Upload pytanga wheels to PyPI via twine.

Detects whether the wheel in dist/ is a pure wheel or contains precompiled
.so files, prints a summary, and prompts for confirmation before uploading.

Usage:
  uv run python tools/upload-pypi.py           # upload most recent wheel
  uv run python tools/upload-pypi.py --check    # inspect wheel only, don't upload
  uv run python tools/upload-pypi.py --repo testpypi  # upload to Test PyPI

Prerequisites:
  uv add --group dev twine
  # Configure ~/.pypirc with your PyPI token or use TWINE_* env vars.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = REPO_ROOT / "dist"


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload pytanga wheels to PyPI")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Inspect the wheel but do not upload.",
    )
    parser.add_argument(
        "--repo",
        default="pypi",
        help="PyPI repository to upload to (default: pypi). Use 'testpypi' for Test PyPI.",
    )
    args = parser.parse_args()

    wheels = sorted(DIST_DIR.glob("tanga_py-*.whl"))
    if not wheels:
        print("No tanga_py wheels found in dist/. Run 'uv build --wheel' first.")
        return 1

    # Take the most recent wheel
    wheel = wheels[-1]
    print(f"Wheel: {wheel.name} ({(wheel.stat().st_size / 1024):.0f} KB)")

    # Check for precompiled .so files
    has_precompiled = False
    precompiled_count = 0
    try:
        import zipfile

        with zipfile.ZipFile(wheel) as z:
            for name in z.namelist():
                if name.startswith("pytanga/precompiled/") and name.endswith(
                    (".so", ".dylib", ".pyd")
                ):
                    has_precompiled = True
                    precompiled_count += 1
                    print(f"  precompiled: {Path(name).name}")
    except Exception:
        pass

    if has_precompiled:
        print(
            f"\nPLATFORM-SPECIFIC wheel with {precompiled_count} precompiled"
            " binding(s)."
        )
        print(
            "This wheel will only work on the platform where it was built"
            " (same OS, arch, Python ABI)."
        )
        if "none-any" in wheel.name:
            print(
                "\n!!  WARNING: Wheel tag is still 'py3-none-any'!"
                " Run 'uv run python tools/fix-wheel-tag.py' before uploading."
            )
    else:
        print("\nPURE Python wheel (py3-none-any).")
        print("This wheel works on any platform (no precompiled binaries).")

    if args.check:
        return 0

    response = input(f"\nUpload to {args.repo}? [y/N]: ").strip().lower()
    if response != "y":
        print("Aborted.")
        return 0

    cmd = ["uv", "run", "twine", "upload", "--repository", args.repo, str(wheel)]
    print(f"\nRunning: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print("Upload complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
