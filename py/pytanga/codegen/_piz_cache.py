# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Cache/load helper for the fixed ``binding_piz`` extension.

``binding_piz`` has a single fixed identity (unlike the algebra bindings, which
are keyed on ``(dim, sig, dtype)``): its cache key is the SHA-256 of
``binding_piz.cpp`` + ``CMakeLists.txt``.  On a miss we try a bundled
``precompiled/`` binary, then fall back to JIT compilation.  Every failure
returns ``None`` so callers can degrade to the pure-Python path.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

from ._build import build_binding
from ._cache import _load, cache_root

_HERE = Path(__file__).resolve().parent
_MODULE_NAME = "binding_piz"
_CPP = _HERE / f"{_MODULE_NAME}.cpp"
_CMAKE = _HERE / "CMakeLists.txt"


def _piz_key() -> str:
    """Return a deterministic digest of the PIZ binding + its CMake build."""
    h = hashlib.sha256()
    h.update(_CPP.read_bytes())
    h.update(_CMAKE.read_bytes())
    return h.hexdigest()


def _precompiled_dir() -> Path | None:
    """Return the ``precompiled/`` dir (wheel or repo) if it has a manifest."""
    pkg = _HERE.parent / "precompiled"
    repo = _HERE.parent.parent.parent / "precompiled"
    for candidate in (pkg, repo):
        if (candidate / "manifest.json").exists():
            return candidate
    return None


def get_or_build_piz(*, verbose: bool = False) -> ModuleType | None:
    """Return the loaded ``binding_piz`` module, or ``None`` if unavailable.

    Priority: cache hit → precompiled bundle → JIT build.  Build/load failures
    return ``None`` (never raise) so the caller can fall back to numpy.
    """
    key = _piz_key()
    entry = cache_root() / key
    entry.mkdir(parents=True, exist_ok=True)

    # --- cache hit ---
    meta = entry / "meta.json"
    if meta.exists():
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
            so = entry / str(data["so_path"])
            if so.exists():
                return _load(so, _MODULE_NAME)
        except (OSError, ValueError, KeyError, ImportError):
            pass

    # --- precompiled bundle ---
    precompiled = _precompiled_dir()
    if precompiled is not None:
        try:
            manifest = json.loads(
                (precompiled / "manifest.json").read_text(encoding="utf-8")
            )
            piz_entry = manifest.get("piz", {})
            precompiled_key = piz_entry.get("key", "")
            if not precompiled_key or precompiled_key == key:
                for candidate in precompiled.iterdir():
                    if (
                        candidate.name.startswith(f"{_MODULE_NAME}.")
                        and candidate.suffix in (".so", ".pyd")
                    ):
                        dest = entry / candidate.name
                        shutil.copy2(candidate, dest)
                        (entry / "meta.json").write_text(
                            json.dumps(
                                {
                                    "module_name": _MODULE_NAME,
                                    "so_path": candidate.name,
                                    "key": key,
                                    "timestamp": datetime.now(UTC).isoformat(),
                                    "source": "precompiled",
                                },
                                indent=2,
                            ),
                            encoding="utf-8",
                        )
                        return _load(dest, _MODULE_NAME)
        except (OSError, ValueError, ImportError):
            pass

    # --- JIT build ---
    try:
        so = build_binding(
            _CPP, entry / "cmake_build", _MODULE_NAME, verbose=verbose
        )
    except Exception:
        return None

    rel_so = so.relative_to(entry)
    (entry / "meta.json").write_text(
        json.dumps(
            {
                "module_name": _MODULE_NAME,
                "so_path": rel_so.as_posix(),
                "key": key,
                "timestamp": datetime.now(UTC).isoformat(),
                "source": "jit",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    try:
        return _load(so, _MODULE_NAME)
    except Exception:
        return None
