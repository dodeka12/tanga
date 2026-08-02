# Repository Restructure — Migration Plan

## Goal

Migrate the repository from the old flat layout (with `pytanga/` at the root) to the
new layout described below, and rename `source/` to `cpp/`.  All Python tooling, imports,
and CMake paths must be updated to match.

---

## Target Directory Layout

```
<repo>/
├── CMakeLists.txt               # root CMake — needs subdirectory paths updated
├── pyproject.toml               # needs package path + pytest config
├── main.py                      # trivial stub (no changes needed)
│
├── cpp/                         # ← renamed from source/
│   ├── Tan.Core/
│   ├── Tan.Math/
│   ├── Tan.GA/
│   ├── Tan.Crypt/
│   ├── Tan.Crypt.Test/
│   └── Tan.App.Test/
│
├── py/                          # all Python lives here (NOT a Python package itself)
│   ├── cmake/
│   │   └── binding/
│   │       └── CMakeLists.txt   # binding cmake — no changes needed
│   ├── examples/
│   │   └── basis_demo.py        # needs import fix
│   ├── pytanga/                 # ← the installable package root
│   │   ├── __init__.py
│   │   ├── algebra.py           # ← renamed from _algebra.py
│   │   ├── _blade_names.py
│   │   ├── _build.py            # needs REPO_ROOT + BINDING_CMAKE + TANGA_SOURCE fixes
│   │   ├── _cache.py            # needs one import fix (inside precompile())
│   │   ├── _codegen.py
│   │   ├── _mv.py
│   │   ├── _template.cpp
│   │   ├── _util.py
│   │   └── basis/
│   │       ├── __init__.py      # needs relative imports
│   │       ├── e3.py            # ← renamed from _e3.py; needs import fixes
│   │       ├── n3.py            # ← renamed from _n3.py; needs import fixes
│   │       ├── p3.py            # ← renamed from _p3.py; needs import fixes
│   │       └── pga3.py          # ← renamed from _pga3.py; needs import fixes
│   └── tests/                   # ← moved from pytanga/tests/
│       ├── __init__.py
│       ├── test_algebra_e3.py   # needs import fix
│       ├── test_basis.py        # needs import fix
│       ├── test_blade_names.py  # needs import fix
│       ├── test_cache.py        # needs import fix
│       └── test_modular.py      # needs import fix
│
├── dev/
│   ├── src/
│   │   └── test_phase4.py       # needs import fix
│   └── todos/
│       └── pytanga/
│           └── *.md
│
└── docs/                        # unchanged
    ├── dev/
    ├── py/
    └── user/
```

**Orphan files to delete:**
- `py/_algebra.py` — old pre-restructure copy of `algebra.py`, no longer needed

---

## Import Convention After Migration

`py/` is NOT a Python package (no `__init__.py`).  
`py/` is added to `sys.path` via `[tool.pytest.ini_options] pythonpath = ["py"]`  
and via `uv run --directory py python ...` (or a `PYTHONPATH=py` prefix).

All imports therefore use `pytanga` directly:

```python
from pytanga import Algebra          # ✓  (not from py.pytanga import ...)
from pytanga.basis import BasisE3    # ✓
import pytanga                       # ✓
```

Within the package, use **relative imports** (already the case for `_cache.py`, `algebra.py`,
`_mv.py`, `_util.py`):

```python
from .algebra import Algebra         # inside basis/e3.py
from pytanga._mv import MV                 # inside basis/e3.py
from ._codegen import generate       # inside _build.py
```

---

## Changes Needed

### Step 1 — Rename `source/` → `cpp/` ✓

| Action | Detail |
|--------|--------|
| Rename directory | `mv source/ cpp/` |

---

### Step 2 — Update root `CMakeLists.txt` ✓

Five `add_subdirectory` calls reference `source/`:

| Old | New |
|-----|-----|
| `add_subdirectory(source/Tan.Core)` | `add_subdirectory(cpp/Tan.Core)` |
| `add_subdirectory(source/Tan.Math)` | `add_subdirectory(cpp/Tan.Math)` |
| `add_subdirectory(source/Tan.GA)` | `add_subdirectory(cpp/Tan.GA)` |
| `add_subdirectory(source/Tan.Crypt.Test)` | `add_subdirectory(cpp/Tan.Crypt.Test)` |
| `add_subdirectory(source/Tan.App.Test)` | `add_subdirectory(cpp/Tan.App.Test)` |

---

### Step 3 — Update `pyproject.toml` ✓

**a) Wheel package path**

```toml
# Old
[tool.hatch.build.targets.wheel]
packages = ["pytanga"]

# New
[tool.hatch.build.targets.wheel]
packages = ["py/pytanga"]
```

**b) Add pytest configuration**

```toml
[tool.pytest.ini_options]
testpaths  = ["py/tests"]
pythonpath = ["py"]        # puts py/ on sys.path so "import pytanga" works
```

**c) Clean up duplicate `dev` dependency group** (currently `dev` appears twice —
once under `[project.optional-dependencies]` and once under `[dependency-groups]`).
Consolidate into `[dependency-groups]` only, or keep both but ensure they stay in sync.

---

### Step 4 — Fix `py/pytanga/_build.py` path computations ✓

Two module-level constants need updating:

| Constant | Old computation | Issue | New computation |
|----------|----------------|-------|----------------|
| `_REPO_ROOT` | `Path(__file__).parent.parent` | `py/pytanga/../../` = `py/` not repo root | `Path(__file__).parent.parent.parent` |
| `TANGA_SOURCE` (default) | `_REPO_ROOT / "source"` | Directory renamed to `cpp/` | `_REPO_ROOT / "cpp"` |
| `_BINDING_CMAKE` | `Path(__file__).parent / "cmake" / "binding" / …` | Points to `py/pytanga/cmake/` which doesn't exist | `Path(__file__).parent.parent / "cmake" / "binding" / …` (= `py/cmake/binding/…`) |

Also one broken lazy import inside `build_and_load()`:

```python
# Old (line ~89):
from py.pytanga._codegen import generate, module_name as mk_module_name

# New (relative):
from ._codegen import generate, module_name as mk_module_name
```

---

### Step 5 — Fix imports inside `py/pytanga/` (internal package) ✓

#### `py/pytanga/algebra.py`
| Line | Old | New |
|------|-----|-----|
| ~61 | `from py.basis import _CLASS_MAP` | `from .basis import _CLASS_MAP` |

#### `py/pytanga/_cache.py`
| Line | Old | New |
|------|-----|-----|
| ~165 | `from py.pytanga._cache import get_or_build` | `from ._cache import get_or_build` |

#### `py/pytanga/basis/__init__.py`
Currently uses absolute `pytanga.basis.e3` imports. These will work once `py/` is on
`sys.path`, but are inconsistent with the rest of the package. Change to relative:

| Old | New |
|-----|-----|
| `from pytanga.basis.e3 import BasisE3` | `from .e3 import BasisE3` |
| `from pytanga.basis.p3 import BasisP3` | `from .p3 import BasisP3` |
| `from pytanga.basis.n3 import BasisN3` | `from .n3 import BasisN3` |
| `from pytanga.basis.pga3 import BasisPGA3` | `from .pga3 import BasisPGA3` |

#### `py/pytanga/basis/e3.py`
| Old | New |
|-----|-----|
| `from py.pytanga.algebra import Algebra` | `from pytanga.algebra import Algebra` |
| `from py.pytanga._mv import MV` | `from pytanga._mv import MV` |
| `from py.pytanga._util import build_display_basis` *(lazy, inside method)* | `from pytanga._util import build_display_basis` |
| `from py.pytanga._util import format_in_basis` *(lazy, inside method)* | `from pytanga._util import format_in_basis` |

#### `py/pytanga/basis/p3.py`  *(same four-import pattern as e3.py)*
| Old | New |
|-----|-----|
| `from py.pytanga.algebra import Algebra` | `from pytanga.algebra import Algebra` |
| `from py.pytanga._mv import MV` | `from pytanga._mv import MV` |
| `from py.pytanga._util import build_display_basis` | `from pytanga._util import build_display_basis` |
| `from py.pytanga._util import format_in_basis` | `from pytanga._util import format_in_basis` |

#### `py/pytanga/basis/n3.py`  *(same four-import pattern)*
| Old | New |
|-----|-----|
| `from py.pytanga.algebra import Algebra` | `from pytanga.algebra import Algebra` |
| `from py.pytanga._mv import MV` | `from pytanga._mv import MV` |
| `from py.pytanga._util import build_display_basis` | `from pytanga._util import build_display_basis` |
| `from py.pytanga._util import format_in_basis` | `from pytanga._util import format_in_basis` |

#### `py/pytanga/basis/pga3.py`
| Old | New |
|-----|-----|
| `from py.basis.basis_n3 import BasisN3, _EP, _EM` | `from .n3 import BasisN3, _EP, _EM` |
| `from py.pytanga._mv import MV` | `from pytanga._mv import MV` |

*(Note: `basis_n3` → `n3` is also a filename rename that already happened.)*

---

### Step 6 — Fix imports in `py/tests/` ✓

All test files currently use `from py.pytanga.xxx` or `import py.pytanga`.
After `pythonpath = ["py"]` is set in `pyproject.toml`, change all to plain `pytanga`:

| File | Old | New |
|------|-----|-----|
| `test_algebra_e3.py` | `import py.pytanga as pytanga` | `import pytanga` |
| `test_modular.py` | `import py.pytanga as pytanga` | `import pytanga` |
| `test_basis.py` | `from py.pytanga import Algebra` | `from pytanga import Algebra` |
| `test_basis.py` | `from py.basis import BasisE3, …` | `from pytanga.basis import BasisE3, …` |
| `test_blade_names.py` | `from py.pytanga._blade_names import …` | `from pytanga._blade_names import …` |
| `test_cache.py` (×10 occurrences) | `from py.pytanga._cache import …` | `from pytanga._cache import …` |

---

### Step 7 — Fix imports in scripts ✓

| File | Old | New |
|------|-----|-----|
| `py/examples/basis_demo.py` | `from py.basis import BasisE3, …` | `from pytanga.basis import BasisE3, …` |
| `dev/src/test_phase4.py` | `from py.pytanga._build import build_and_load` | `from pytanga._build import build_and_load` |

---

### Step 8 — Delete orphan file ✓

| File | Reason |
|------|--------|
| `py/_algebra.py` | Leftover copy from before `_algebra.py` was moved and renamed to `py/pytanga/algebra.py`. Has stale `from .pytanga.xxx` imports. Safe to delete. |

---

### Step 9 — Verify `py/cmake/binding/CMakeLists.txt` ✓

This file receives `TANGA_SOURCE` as a `-D` cmake variable and does not hardcode the
source directory name.  After Step 4 fixes the default in `_build.py`, this file
requires **no changes**.

Internal structure summary:
- `${TANGA_SOURCE}/Tan.Math/ValuePrecision.cpp` — resolved at cmake time from caller
- `${TANGA_SOURCE}/Tan.Core/ValueFormatString.cpp` — same
- `${TANGA_SOURCE}/Tan.Math/Matrix.Enum.cpp` — same
- `target_include_directories(… "${TANGA_SOURCE}")` — same

✓ No changes needed.

---

### Step 10 — Smoke-test after all changes ✓

```bash
# Run all unit tests
uv run python -m pytest py/tests/ -q

# Run the demo example
PYTHONPATH=py uv run python py/examples/basis_demo.py

# Confirm cmake still configures
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
```

---

## Summary Table

| # | Scope | File(s) | Type of change |
|---|-------|---------|----------------|
| 1 | File system | `source/` → `cpp/` | Directory rename |
| 2 | C++ build | `CMakeLists.txt` (root) | 5 path strings |
| 3 | Python packaging | `pyproject.toml` | Package path + pytest config |
| 4 | Python build | `py/pytanga/_build.py` | 3 path constants + 1 import |
| 5 | Package internals | `py/pytanga/algebra.py`, `_cache.py`, `basis/__init__.py`, `basis/e3.py`, `basis/p3.py`, `basis/n3.py`, `basis/pga3.py` | Import fixes (13 broken lines) |
| 6 | Tests | `py/tests/test_*.py` (5 files, ~14 lines) | Import fixes |
| 7 | Scripts | `py/examples/basis_demo.py`, `dev/src/test_phase4.py` | Import fixes |
| 8 | Cleanup | `py/_algebra.py` | Delete orphan |
| 9 | CMake binding | `py/cmake/binding/CMakeLists.txt` | No changes needed |
| 10 | Verification | — | Smoke-test |
