#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Build a single precompiled algebra binding and place it in precompiled/.

Usage:
  uv run python tools/build-algebra.py
  uv run python tools/build-algebra.py --dim 4 --sig 8
  uv run python tools/build-algebra.py --dim 5 --sig 16 --dtype float64 --verbose
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PRECOMPILED_DIR = REPO_ROOT / "precompiled"

_DEFAULT_DIM = 3
_DEFAULT_SIG = 0
_DEFAULT_DTYPE = "float64"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a precompiled algebra binding.")
    parser.add_argument(
        "--dim",
        type=int,
        default=_DEFAULT_DIM,
        help=f"Dimension (default: {_DEFAULT_DIM})",
    )
    parser.add_argument(
        "--sig",
        type=int,
        default=_DEFAULT_SIG,
        help=f"Signature (default: {_DEFAULT_SIG}, binary like 0b1000 works)",
    )
    parser.add_argument(
        "--dtype",
        default=_DEFAULT_DTYPE,
        help=f"Data type — float64 or int64 (default: {_DEFAULT_DTYPE})",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show full CMake configure and compiler output",
    )
    args = parser.parse_args()

    import pytanga.codegen._cache as cache_mod
    from pytanga.codegen._cache import _make_key
    from pytanga.codegen._generator import module_name

    dim, sig, dtype = args.dim, args.sig, args.dtype
    mod_name = module_name(dim, sig, dtype)
    key = _make_key(dim, sig, dtype)

    # Validate dtype
    if dtype not in ("float64", "int64"):
        print(f"ERROR: dtype must be 'float64' or 'int64', got '{dtype}'")
        return 1

    # Ensure precompiled dir exists
    PRECOMPILED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Building algebra: dim={dim}, sig={sig} (0b{sig:b}), dtype={dtype}")
    print(f"Module name: {mod_name}")
    print()

    # Compile (or use cached)
    try:
        cache_mod.get_or_build(dim, sig, dtype, verbose=args.verbose)
    except Exception as exc:
        print(f"ERROR: compilation failed: {exc}")
        return 1

    # Find the compiled extension in the cache
    cache_root = cache_mod.cache_root()
    so_path = None
    for cache_dir in sorted(cache_root.iterdir()):
        if not cache_dir.is_dir():
            continue
        meta_path = cache_dir / "meta.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text())
        if meta.get("module_name") == mod_name:
            so_path = cache_dir / meta["so_path"]
            if so_path.is_file():
                break
            so_path = None

    if so_path is None:
        print(f"ERROR: compiled extension not found in cache for {mod_name}")
        return 1

    # Copy to precompiled/
    dest = PRECOMPILED_DIR / so_path.name
    shutil.copy2(so_path, dest)
    print(f"Copied: {so_path.name} -> precompiled/")

    # Update manifest.json
    manifest_path = PRECOMPILED_DIR / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
    else:
        manifest = {
            "version": 1,
            "platform": platform.platform(),
            "python_abi": f"cp{sys.version_info.major}{sys.version_info.minor}",
            "compiler": _detect_compiler(),
            "algebras": {},
        }

    manifest["algebras"][mod_name] = {
        "dim": dim,
        "sig": sig,
        "dtype": dtype,
        "key": key,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"Manifest updated: {manifest_path}")
    print()
    print("Done. Precompiled dir contents:")
    for f in sorted(PRECOMPILED_DIR.iterdir()):
        if f.name != "manifest.json":
            print(f"  {f.name}")

    return 0


def _detect_compiler() -> str:
    """Detect installed C++ compiler (brief label)."""
    # On Windows, probe MSVC first
    if platform.system() == "Windows":
        try:
            out = subprocess.run(["cl"], capture_output=True, text=True, timeout=5)
            if out.returncode == 0 or out.stdout:
                return out.stdout.splitlines()[0] if out.stdout else "MSVC"
            return "unknown"
        except Exception:
            pass

    # Linux / macOS / fallback
    try:
        out = subprocess.run(
            ["g++", "--version"], capture_output=True, text=True, timeout=5
        )
        return out.stdout.splitlines()[0] if out.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
