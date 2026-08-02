#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Build precompiled bindings for common algebras and bundle them into the package.

Usage:
  uv run python tools/build-precompiled.py
  uv build --wheel
"""

from __future__ import annotations

import json
import platform
import shutil
import sys
from pathlib import Path

ALGEBRAS = [
    # (dim, sig, dtype, description)
    (3, 0, "float64", "E3"),
    (4, 8, "float64", "P3/PGA3"),
    (5, 16, "float64", "N3"),
    (3, 0, "int64", "E3 (modular)"),
    (10, 0, "int64", "Sparse high-dim"),
]

REPO_ROOT = Path(__file__).resolve().parent.parent
PRECOMPILED_DIR = REPO_ROOT / "precompiled"


def main() -> int:
    import pytanga.codegen._cache as cache_mod

    PRECOMPILED_DIR.mkdir(parents=True, exist_ok=True)

    manifest: dict = {
        "version": 1,
        "platform": platform.platform(),
        "python_abi": f"cp{sys.version_info.major}{sys.version_info.minor}",
        "compiler": _detect_compiler(),
        "algebras": {},
    }

    for dim, sig, dtype, desc in ALGEBRAS:
        print(f"Compiling {desc} (dim={dim}, sig={sig}, dtype={dtype})...")
        cache_mod.get_or_build(dim, sig, dtype, verbose=False)

        # Find the .so in cache
        from pytanga.codegen._cache import _make_key
        from pytanga.codegen._generator import module_name

        mod_name = module_name(dim, sig, dtype)
        key = _make_key(dim, sig, dtype)
        cache_root = cache_mod.cache_root()

        # Walk cache dirs looking for the matching .so
        so_copied = False
        for cache_dir in cache_root.iterdir():
            if not cache_dir.is_dir():
                continue
            meta_path = cache_dir / "meta.json"
            if not meta_path.exists():
                continue
            meta = json.loads(meta_path.read_text())
            if meta.get("module_name") == mod_name:
                so_path = cache_dir / meta["so_path"]
                if so_path.is_file():
                    dest = PRECOMPILED_DIR / so_path.name
                    shutil.copy2(so_path, dest)
                    manifest["algebras"][mod_name] = {
                        "dim": dim,
                        "sig": sig,
                        "dtype": dtype,
                        "key": key,
                    }
                    print(f"  -> bundled {so_path.name}")
                    so_copied = True
                break

        if not so_copied:
            print(f"  WARNING: .so not found in cache for {mod_name}")

    # Write manifest
    manifest_path = PRECOMPILED_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\nManifest written to {manifest_path}")
    print(f"Precompiled .so files in {PRECOMPILED_DIR}:")
    for f in sorted(PRECOMPILED_DIR.iterdir()):
        if f.name != "manifest.json":
            print(f"  {f.name}")

    return 0


def _detect_compiler() -> str:
    import subprocess

    try:
        out = subprocess.run(
            ["g++", "--version"], capture_output=True, text=True, timeout=5
        )
        return out.stdout.splitlines()[0] if out.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
