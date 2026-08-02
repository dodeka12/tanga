# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Cache layer for compiled extension modules."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

from ._build import TANGA_SOURCE, build_and_load
from ._generator import module_name as mk_module_name

__all__ = [
    "_make_key",
    "cache_root",
    "clear",
    "get_or_build",
    "invalidate",
    "lookup",
    "precompile",
]


def _make_key(dim: int, sig: int, dtype: str) -> str:
    """Compute a deterministic hex digest that changes when algebra
    parameters or any tanga header (or the binding template) change.
    """
    h = hashlib.sha256()

    # Algebra identity
    h.update(
        json.dumps({"dim": dim, "sig": sig, "dtype": dtype}, sort_keys=True).encode()
    )

    # Content of every .h file under the three bundled source dirs, sorted.
    # We scope to Tan.GA/Tan.Math/Tan.Core only — the same directories that
    # are force-included in the wheel. This ensures the cache key is identical
    # between dev checkouts (repo cpp/) and installed wheels (pytanga/_ga_src/).
    for subdir in ("Tan.GA", "Tan.Math", "Tan.Core"):
        dirpath = (TANGA_SOURCE / subdir).resolve()
        for p in sorted(dirpath.rglob("*.h")):
            if p.name.startswith("_CompileTest_"):
                continue
            h.update(p.read_bytes())

    # Content of the binding template
    template = Path(__file__).parent.parent / "_template.cpp"
    h.update(template.read_bytes())

    # Content of codegen files that affect generated C++ code.
    # We intentionally exclude _build.py and _cache.py — changes to
    # the build/cache infrastructure don't invalidate precompiled .so
    # files because the generated C++ is identical.
    _CODEGEN_FILES = [
        "_generator.py",
        "_blade_masks.py",
        "_blade_ops.py",
        "_float_products.py",
        "_int_products.py",
        "_matrix.py",
        "_mv_operators.py",
        "_tensor.py",
        "_utils.py",
    ]
    codegen_dir = Path(__file__).parent
    for fn in _CODEGEN_FILES:
        p = codegen_dir / fn
        h.update(p.read_bytes())

    return h.hexdigest()


def cache_root() -> Path:
    """Return the root cache directory.

    Respects the PYTANGA_CACHE_DIR environment variable.
    """
    default = Path.home() / ".cache" / "pytanga"
    return Path(os.environ.get("PYTANGA_CACHE_DIR", default))


def lookup(dim: int, sig: int, dtype: str) -> Path | None:
    """Return the path to the compiled extension if cached, else None."""
    key = _make_key(dim, sig, dtype)
    meta = cache_root() / key / "meta.json"

    if not meta.exists():
        return None

    data = json.loads(meta.read_text(encoding="utf-8"))
    so = cache_root() / key / data["so_path"]

    if not so.exists():
        return None

    return so


def _load_precompiled(dim: int, sig: int, dtype: str, key: str, entry_dir: Path):
    """Try to use a precompiled .so from pytanga/precompiled/.

    Returns the loaded module on success, or None if no matching
    precompiled binary exists (or if it is incompatible).
    """
    # Check both the wheel-bundled location and the repo-root location
    pkg_precompiled = Path(__file__).parent.parent / "precompiled"
    repo_precompiled = Path(__file__).parent.parent.parent.parent / "precompiled"

    precompiled_dir = None
    for candidate in (pkg_precompiled, repo_precompiled):
        if (candidate / "manifest.json").exists():
            precompiled_dir = candidate
            break

    if precompiled_dir is None:
        return None

    manifest_path = precompiled_dir / "manifest.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mod_name = mk_module_name(dim, sig, dtype)
    entry = manifest.get("algebras", {}).get(mod_name)

    if entry is None:
        return None

    # Find the .so file by prefix (handles ABI tags like .cpython-312-x86_64-linux-gnu.so)
    so_path = None
    prefix = f"{mod_name}."
    for candidate in precompiled_dir.iterdir():
        if candidate.name.startswith(prefix) and candidate.suffix in (".so", ".pyd"):
            so_path = candidate
            break
    if so_path is None:
        return None

    so_name = so_path.name

    # Precompiled key — the cache key computed when the .so was built.
    # If the current source headers differ from when the precompiled .so
    # was built, skip it and fall through to JIT compilation.
    precompiled_key = entry.get("key", "")
    if precompiled_key and precompiled_key != key:
        return None

    # Copy into cache so subsequent imports use the cache path
    import shutil

    try:
        dest = entry_dir / so_name
        shutil.copy2(so_path, dest)
        rel_so = Path(so_name)
        meta = {
            "dim": dim,
            "sig": sig,
            "dtype": dtype,
            "key": key,
            "module_name": mod_name,
            "so_path": rel_so.as_posix(),
            "timestamp": datetime.now(UTC).isoformat(),
            "source": "precompiled",
        }
        (entry_dir / "meta.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )
    except OSError:
        return None

    return _load(dest, mod_name)


def get_or_build(
    dim: int,
    sig: int,
    dtype: str,
    *,
    verbose: bool = False,
):
    """Return a loaded Python module for (dim, sig, dtype).

    On a cache hit, loads and returns the cached extension immediately.
    On a miss, checks for a precompiled .so bundled in the wheel, then
    falls back to compiling the extension on the fly.
    """

    so_path = lookup(dim, sig, dtype)
    mod_name = mk_module_name(dim, sig, dtype)

    if so_path is not None:
        return _load(so_path, mod_name)

    # --- cache miss: try precompiled, then compile ---
    key = _make_key(dim, sig, dtype)
    entry = cache_root() / key
    entry.mkdir(parents=True, exist_ok=True)

    # Precompiled check — try a pre-bundled .so before compiling
    try:
        module = _load_precompiled(dim, sig, dtype, key, entry)
        if module is not None:
            return module
    except Exception:
        pass  # precompiled load failed → compile normally

    module, so_path = build_and_load(
        dim,
        sig,
        dtype,
        build_dir=entry,
        tanga_source=TANGA_SOURCE,
        verbose=verbose,
    )

    mod_name = mk_module_name(dim, sig, dtype)
    rel_so = so_path.relative_to(entry)

    meta = {
        "dim": dim,
        "sig": sig,
        "dtype": dtype,
        "key": key,
        "module_name": mod_name,
        "so_path": rel_so.as_posix(),
        "timestamp": datetime.now(UTC).isoformat(),
    }
    (entry / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return module


def _load(so_path: Path, module_name: str):
    """Load a previously compiled extension by path."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, so_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def invalidate(dim: int, sig: int, dtype: str) -> None:
    """Remove the cache entry for one (dim, sig, dtype) if it exists."""
    key = _make_key(dim, sig, dtype)
    entry = cache_root() / key
    if entry.exists():
        shutil.rmtree(entry)


def clear() -> None:
    """Remove the entire pytanga cache directory."""
    root = cache_root()
    if root.exists():
        shutil.rmtree(root)


def precompile(
    algebras: list[tuple[int, int, str]],
    *,
    max_workers: int | None = None,
    verbose: bool = False,
) -> None:
    """
    Compile a list of (dim, sig, dtype) tuples in parallel.

    Example
    -------
    pytanga.precompile([
        (3, 0, "float64"),
        (4, 0b1000, "float64"),
        (5, 0b10000, "float64"),
    ])
    """
    from . import get_or_build

    def _build_one(args):
        dim, sig, dtype = args
        get_or_build(dim, sig, dtype, verbose=verbose)
        return (dim, sig, dtype)

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_build_one, a): a for a in algebras}
        for future in as_completed(futures):
            dim, sig, dtype = futures[future]
            try:
                future.result()
                print(f"  compiled G({dim},{sig:#b}) dtype={dtype}")
            except Exception as exc:
                print(f"  FAILED G({dim},{sig:#b}) dtype={dtype}: {exc}")
