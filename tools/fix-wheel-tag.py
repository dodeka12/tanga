#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Patch the wheel platform tag when precompiled .so files are bundled.

hatchling produces py3-none-any because the .so files in precompiled/
are not recognized as Python extension modules. This script detects
precompiled binaries and rewrites the wheel filename and WHEEL metadata
to include the correct platform tag.

Usage:
  uv build --wheel -o /tmp/dist
  uv run python tools/fix-wheel-tag.py -d /tmp/dist

The fixed wheel is written back to the same directory. For a full manylinux
build, use auditwheel in a manylinux container instead.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fix the wheel platform tag for precompiled wheels."
    )
    parser.add_argument(
        "-d",
        "--wheel-dir",
        default=str(REPO_ROOT / "dist"),
        help="Directory containing the wheel (default: dist/)",
    )
    args = parser.parse_args()

    wheel_dir = Path(args.wheel_dir)
    wheels = sorted(wheel_dir.glob("tanga_py-*.whl"))
    if not wheels:
        print(f"No tanga_py wheels in {wheel_dir}. Run 'uv build --wheel' first.")
        return 1

    wheel = wheels[-1]

    # Check if the wheel actually contains precompiled .so files
    has_precompiled = False
    with zipfile.ZipFile(wheel) as z:
        for name in z.namelist():
            if name.startswith("pytanga/precompiled/") and name.endswith(
                (".so", ".pyd")
            ):
                has_precompiled = True
                break

    if not has_precompiled:
        print(f"Wheel {wheel.name} has no precompiled .so — tag is correct.")
        return 0

    # Don't re-tag if already platform-specific
    if "none-any" not in wheel.name:
        print(f"Wheel {wheel.name} already has a platform-specific tag.")
        return 0

    # Compute the platform tag from the current environment
    tag = _platform_tag()
    new_name = wheel.name.replace("py3-none-any", tag)
    new_path = wheel_dir / new_name

    if new_path.exists():
        new_path.unlink()

    # Copy and rewrite the WHEEL metadata inside the zip
    _rewrite_wheel_tag(wheel, new_path, tag)

    # Remove the original (untagged) wheel
    wheel.unlink()

    print(f"  {wheel.name}  ->  {new_name}")
    print(f"Platform tag: {tag}")
    return 0


def _platform_tag() -> str:
    """Build a platform tag string from the current interpreter and OS."""
    import platform

    py_ver = f"cp{sys.version_info.major}{sys.version_info.minor}"
    abi_tag = f"cp{sys.version_info.major}{sys.version_info.minor}"

    machine = platform.machine()  # "x86_64", "aarch64"
    system = platform.system()  # "Linux", "Darwin"

    if system == "Linux":
        plat_tag = f"manylinux_2_35_{machine}"
    elif system == "Darwin":
        # macOS version from platform
        mac_ver = platform.mac_ver()[0]  # e.g. "14.0"
        major = mac_ver.split(".")[0] if mac_ver else "14"
        plat_tag = f"macosx_{major}_0_{machine}"
    elif system == "Windows":
        plat_tag = "win_amd64" if machine.endswith("64") else "win32"
    else:
        plat_tag = f"{system.lower()}_{machine}"

    return f"{py_ver}-{abi_tag}-{plat_tag}"


def _rewrite_wheel_tag(src: Path, dst: Path, tag: str) -> None:
    """Copy the wheel, rewriting the WHEEL metadata with the new tag."""
    # The tag format is "py_version-abi_tag-platform_tag"
    tags = tag.split("-")
    with (
        zipfile.ZipFile(src, "r") as zin,
        zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout,
    ):
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.endswith(".dist-info/WHEEL"):
                text = data.decode("utf-8")
                # Replace the Tag line
                lines = []
                for line in text.splitlines():
                    if line.startswith("Tag: "):
                        lines.append(f"Tag: {tag}")
                    else:
                        lines.append(line)
                data = "\n".join(lines).encode("utf-8")
            zout.writestr(item, data)


if __name__ == "__main__":
    raise SystemExit(main())
