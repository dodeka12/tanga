# Phase 5 — Cache Layer

**Overview plan:** [plan.md](plan.md)  
**Depends on:** Phase 3 (module naming), Phase 4 (build_and_load)  
**Required by:** Phase 6 (facade uses cache to skip recompilation)

---

## Goal

Implement `pytanga/_cache.py` — store compiled extension modules under
`~/.cache/pytanga/` so that a given `(dim, sig, dtype)` is only compiled once
per tanga version.

---

## Cache design

```
~/.cache/pytanga/
  <hash>/
    binding_dim3_sig0_f64.cpp      # generated source (kept for debugging)
    cmake_build/                   # cmake working directory
      binding_dim3_sig0_f64.pyd   # (or .so)
    meta.json
```

**Cache key** — SHA-256 of the tuple:
- `dim` (int)
- `sig` (int)
- `dtype` (str)
- Content hash of every `.h` file under `TANGA_SOURCE` and
  `pytanga/_template.cpp`, sorted by relative path.

This ensures the cache is automatically invalidated when tanga headers or the
binding template change.

**`meta.json` schema:**
```json
{
  "dim":       3,
  "sig":       0,
  "dtype":     "float64",
  "key":       "<hex sha256>",
  "module_name": "binding_dim3_sig0_f64",
  "so_path":   "cmake_build/binding_dim3_sig0_f64.pyd",
  "timestamp": "2026-06-27T12:34:56"
}
```

---

## Steps

### 5.1 Implement `_make_key()`

```python
import hashlib
import json
from pathlib import Path

from pytanga._build import TANGA_SOURCE
from pytanga._codegen import module_name as mk_module_name


def _make_key(dim: int, sig: int, dtype: str) -> str:
    """
    Compute a deterministic hex digest that changes whenever the algebra
    parameters or any tanga header (or the binding template) changes.
    """
    h = hashlib.sha256()

    # Algebra identity
    h.update(json.dumps({"dim": dim, "sig": sig, "dtype": dtype},
                        sort_keys=True).encode())

    # Content of every .h file under TANGA_SOURCE, sorted for determinism
    header_paths = sorted(TANGA_SOURCE.rglob("*.h"))
    for p in header_paths:
        h.update(p.read_bytes())

    # Content of the binding template
    template = Path(__file__).parent / "_template.cpp"
    h.update(template.read_bytes())

    return h.hexdigest()
```

- [x] Step 5.1

### 5.2 Implement `cache_root()`

```python
import os


def cache_root() -> Path:
    """
    Return the root cache directory.
    Respects the PYTANGA_CACHE_DIR environment variable.
    """
    default = Path.home() / ".cache" / "pytanga"
    return Path(os.environ.get("PYTANGA_CACHE_DIR", default))
```

- [x] Step 5.2

### 5.3 Implement `lookup()`

```python
def lookup(dim: int, sig: int, dtype: str) -> Path | None:
    """
    Return the path to the compiled extension if it is cached, else None.
    Verifies that the file actually exists (guards against manual deletion).
    """
    key  = _make_key(dim, sig, dtype)
    meta = cache_root() / key / "meta.json"

    if not meta.exists():
        return None

    data = json.loads(meta.read_text())
    so   = cache_root() / key / data["so_path"]

    if not so.exists():
        return None   # cache entry is corrupt / partially deleted

    return so
```

- [x] Step 5.3

### 5.4 Implement `get_or_build()`

This is the single entry point called by the facade. It combines lookup,
build, and store.

```python
from datetime import datetime, timezone


def get_or_build(
    dim: int,
    sig: int,
    dtype: str,
    *,
    verbose: bool = False,
):
    """
    Return a loaded Python module for (dim, sig, dtype).

    On a cache hit, loads and returns the cached extension immediately.
    On a miss, compiles the extension, stores it in the cache, then returns it.
    """
    import importlib.util
    from pytanga._build import build_and_load, TANGA_SOURCE
    from pytanga._codegen import module_name as mk_module_name

    so_path = lookup(dim, sig, dtype)

    if so_path is not None:
        return _load(so_path, mk_module_name(dim, sig, dtype))

    # --- cache miss: compile ---
    key      = _make_key(dim, sig, dtype)
    entry    = cache_root() / key
    entry.mkdir(parents=True, exist_ok=True)

    module, so_path = build_and_load(
        dim, sig, dtype,
        build_dir=entry,
        tanga_source=TANGA_SOURCE,
        verbose=verbose,
    )

    # --- so_path is returned directly by build_and_load; no re-discovery needed ---
    mod_name = mk_module_name(dim, sig, dtype)
    rel_so   = so_path.relative_to(entry)

    # --- write meta.json ---
    meta = {
        "dim":         dim,
        "sig":         sig,
        "dtype":       dtype,
        "key":         key,
        "module_name": mod_name,
        "so_path":     rel_so.as_posix(),
        "timestamp":   datetime.now(timezone.utc).isoformat(),
    }
    (entry / "meta.json").write_text(json.dumps(meta, indent=2))

    return module


def _load(so_path: Path, module_name: str):
    import importlib.util
    spec   = importlib.util.spec_from_file_location(module_name, so_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
```

- [x] Step 5.4

### 5.5 Implement `invalidate()` and `clear()`

```python
import shutil


def invalidate(dim: int, sig: int, dtype: str) -> None:
    """Remove the cache entry for one (dim, sig, dtype) if it exists."""
    key   = _make_key(dim, sig, dtype)
    entry = cache_root() / key
    if entry.exists():
        shutil.rmtree(entry)


def clear() -> None:
    """Remove the entire pytanga cache directory."""
    root = cache_root()
    if root.exists():
        shutil.rmtree(root)
```

- [x] Step 5.5

### 5.6 Public API surface

```python
__all__ = ["cache_root", "lookup", "get_or_build", "invalidate", "clear"]
```

- [x] Step 5.6

### 5.7 Test the cache round-trip

```python
from pytanga._cache import get_or_build, lookup, invalidate

# First call: compiles
mod1 = get_or_build(3, 0, "float64", verbose=True)
assert mod1.ALGEBRA_DIM == 8

# Second call: must not recompile — should be instant
mod2 = get_or_build(3, 0, "float64")
assert mod2.ALGEBRA_DIM == 8

# Lookup should now find the entry
assert lookup(3, 0, "float64") is not None

# Invalidate and confirm it's gone
invalidate(3, 0, "float64")
assert lookup(3, 0, "float64") is None
```

- [x] Step 5.7

---

## Completion check

- [x] `pytanga/_cache.py` is fully implemented
- [x] `get_or_build(3, 0, "float64")` compiles on first call (~5–20 s)
- [x] Second call to `get_or_build(3, 0, "float64")` returns in < 1 s
- [x] `invalidate()` removes the entry; subsequent `lookup()` returns `None`
- [x] `clear()` empties `~/.cache/pytanga/` (verify directory is gone)
- [x] Changing a tanga header `.h` mtime (even `touch`) produces a different
  key (verify by printing `_make_key(3, 0, "float64")` before and after)
