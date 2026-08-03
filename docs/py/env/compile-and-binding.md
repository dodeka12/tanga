# Automatic Compile and Binding

pytanga has **no pre-compiled extension bundled with the package**.  Instead,
when you first instantiate an `Algebra` for a particular combination of
`(dim, sig, dtype)`, pytanga automatically generates a C++ source file,
compiles it into a Python extension, caches it on disk, and loads it.
On subsequent uses the cached binary is loaded in milliseconds.

See [`binding_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/binding_demo.py) for a runnable
walkthrough of everything described on this page.

---

## Pipeline

```
Algebra(dim, sig, dtype)
        │
        ▼
  _cache.get_or_build()
        │
        ├── cache hit? ──────────────────► load .so / .pyd  (milliseconds)
        │
        └── cache miss
                │
                ▼
         _codegen.generate()        ← writes <module>.cpp from embedded template
                │
                ▼
         _build.build_binding()     ← CMake + Ninja/Make → .so / .pyd
                │
                ▼
         importlib.util.load()      ← import the compiled extension
                │
                ▼
         cache: write meta.json + .so
```

---

## Code Generation

`pytanga.codegen._generator` emits a complete C++ binding source file with the
concrete values of `dim`, `sig`, and `dtype` substituted. The resulting
`.cpp` file instantiates the C++ template with those parameters.

The generated module name encodes all three parameters, for example:

```
tanga_d3_s0_float64
```

---

## Compilation

`pytanga.codegen._build.build_binding()` runs a minimal CMake project whose
`CMakeLists.txt` is bundled inside the `codegen/` package.  It links the
generated `.cpp` against:

- the TanGA C++ headers (bundled in the wheel under `pytanga/_ga_src/`, or
  from the repo `cpp/` tree in development mode)
- pybind11

The compiler is `g++` (Linux), `clang++` (macOS), or `cl.exe` (Windows/MSVC),
and the build type is `Release`.  If Ninja is available it is used instead of
Make.  See the [installation guide](installation.md#compiler-setup) for
per-platform compiler setup.

Environment variable `PYTANGA_TANGA_SOURCE` overrides the path to the C++
headers. The default resolution order is: environment variable → bundled
sources in the wheel (`pytanga/_ga_src/`) → repo `cpp/` directory.

Build output goes to a `cmake_build/` subdirectory under the cache entry
directory and is not cleaned up, making rebuild-on-change faster.

---

## Cache

The cache lives at `~/.cache/pytanga/` by default.  Set the environment
variable `PYTANGA_CACHE_DIR` to use a different location.

Each cache entry is a directory named after a **SHA-256 hash** (the cache
key) and contains:

| File | Purpose |
|------|---------|
| `<module>.cpp` | Generated C++ source |
| `cmake_build/` | CMake build directory |
| `<module>.so` (or `.pyd`) | Compiled extension |
| `meta.json` | Records `dim`, `sig`, `dtype`, the cache key, and a build timestamp |

### Cache key

The hash is computed from:

- the algebra parameters: `dim`, `sig`, `dtype`
- every `.h` header found under the `TANGA_SOURCE` directory
- all `.py` files in the `codegen/` package

Any change to those inputs **automatically invalidates** the cache entry for
that algebra, triggering a fresh compile on the next import.

### Inspecting the cache

```python
from pytanga._cache import cache_root, lookup, invalidate
import json

root = cache_root()
for meta_path in sorted(root.glob("*/meta.json")):
    m = json.loads(meta_path.read_text())
    print(m["dim"], m["sig"], m["dtype"], m["timestamp"])
```

To remove a specific entry programmatically:

```python
invalidate(dim=3, sig=0, dtype="float64")
```

---

## Compilation Time

The first compile for a new `(dim, sig, dtype)` takes **5–20 seconds**,
dominated by CMake startup and pybind11 template instantiation overhead.
This time is essentially **independent of `dim`** — the C++ template is
instantiated once regardless of algebra dimension.

Subsequent loads of the same algebra are in the **millisecond** range.

---

## Verbose Mode

Pass `verbose=True` to `Algebra(...)` to see the full CMake and compiler
output during compilation:

```python
alg = pytanga.Algebra(3, 0, verbose=True)
```
