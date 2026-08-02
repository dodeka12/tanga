#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Remove precompiled bindings so a subsequent wheel build produces a pure py3-none-any wheel.

Usage:
  uv run python tools/clean-precompiled.py
  uv build --wheel
"""

from __future__ import annotations

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PRECOMPILED_DIR = REPO_ROOT / "precompiled"


def main() -> int:
    if not PRECOMPILED_DIR.exists():
        print(f"Nothing to clean — {PRECOMPILED_DIR} does not exist.")
        return 0

    removed = False
    for item in list(PRECOMPILED_DIR.iterdir()):
        if item.name == ".gitkeep":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
        removed = True
        print(f"  Removed {item.name}")

    if not removed:
        print("Nothing to clean — no precompiled artifacts.")
    else:
        print("Next 'uv build --wheel' will produce a pure py3-none-any wheel.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
