# Fix Example Imports — Plan

All example files under `py/examples/` have not been consistently adapted to pytanga software changes. Specifically, several modules were restructured but the example imports were not updated.

## Summary

| Category | Files Affected |
|---|---|
| `from pytanga.mv import MV` → `from pytanga import MV` | 8 |
| `from pytanga.mv_utils import ...` → `from pytanga.algebra import ...` | 2 |
| Multiple broken imports in `solver_point_line_p3.py` | 1 |
| `alg.random_mv(...)` → `random_mv(alg, ...)` in `solver_rotor_estimation.py` | 1 |
| Private API usage in `binding_demo.py` | 1 |
| **Total files to edit** | **12** (11 unique; `modulus_algebra_single.py` and `solver_point_line_p3.py` overlap on the MV import) |

---

## Group 1: Fix `from pytanga.mv import MV` (8 files)

`pytanga.mv` does not exist. `MV` lives in `pytanga.algebra` and is re-exported from `pytanga`.

**Change:** Replace existing `from pytanga.mv import MV` with the import that makes sense contextually (either `from pytanga import MV` or drop since `pytanga` is already imported):

| File | Current | Fix |
|---|---|---|
| `algebra/modulus_algebra_multi.py:33` | `from pytanga.mv import MV` | Remove line (already has `import pytanga`); add `MV = pytanga.MV` or just use `pytanga.MV` (line 35 already imported, `MV` not used as standalone) — **actually**: `MV` is used on lines 139, 142, 148 etc. Replace with `from pytanga import MV` |
| `algebra/modulus_algebra_single.py:22` | `from pytanga.mv import MV` | `from pytanga import MV` |
| `algebra/mv_demo.py:26` | `from pytanga.mv import MV` | `from pytanga import MV` |
| `basis/basis_usage.py:44` | `from pytanga.mv import MV` | `from pytanga import MV` |
| `basis/base_e3_demo.py:15` | `from pytanga.mv import MV` | `from pytanga import MV` |
| `basis/base_n3_demo.py:15` | `from pytanga.mv import MV` | `from pytanga import MV` |
| `basis/base_p3_demo.py:15` | `from pytanga.mv import MV` | `from pytanga import MV` |
| `basis/base_pga3_demo.py:15` | `from pytanga.mv import MV` | `from pytanga import MV` |

---

## Group 2: Fix `from pytanga.mv_utils import ...` (2 files)

`pytanga.mv_utils` does not exist. `random_mv` and `random_mask` are exported from `pytanga.algebra`.

| File | Current | Fix |
|---|---|---|
| `tensor/basics_01.py:22` | `from pytanga.mv_utils import random_mv` | `from pytanga.algebra import random_mv` |
| `tensor/basics_02.py:22` | `from pytanga.mv_utils import random_mask, random_mv` | `from pytanga.algebra import random_mask, random_mv` |

---

## Group 3: Fix `numerics/solver_point_line_p3.py` (1 file, 3 fixes)

Three imports to fix:

| Line | Current | Fix |
|---|---|---|
| 10 | `from pytanga.mv import MV` | `from pytanga import MV` |
| 11 | `from pytanga.mv_product_matrix import MVProductMatrix` | `from pytanga.matrix import MVProductMatrix` |
| 12 | `from pytanga.enums import EProduct` | `from pytanga.algebra import EProduct` |

Also, line 14 imports `from pytanga.matrix.convert import to_matrix` — this is correct and should be left as-is.

Note: Line 65 uses `product="gp"` (string) where the function accepts `EProduct`. Since `EProduct` is a `StrEnum`, the string `"gp"` works at runtime, but for consistency it should be `EProduct.GP`. This is a minor style fix.

---

## Group 4: Fix `numerics/solver_rotor_estimation.py` (1 file, 1 fix)

`alg.random_mv(...)` is called on line 76, but `random_mv` is a **standalone function** in `pytanga.algebra._mv_utils`, not a method on `Algebra`.

| Line | Current | Fix |
|---|---|---|
| 76 | `vectors = [alg.random_mv(mask=BladeMask(alg, grades=[1]), rng=i) for i in range(n)]` | `vectors = [random_mv(alg, mask=BladeMask(alg, grades=[1]), rng=i) for i in range(n)]` |

Also need to add `from pytanga.algebra import random_mv` (or `from pytanga import random_mv`) to the imports. Currently line 40 imports `from pytanga import Algebra, BladeMask, MVMatrix` — add `random_mv` there, or use `from pytanga.algebra import random_mv`.

---

## Group 5: Fix `binding_demo.py` private API (1 file, 2 fixes)

`binding_demo.py` uses private submodule imports that bypass the public `codegen/__init__.py` API. The user has confirmed `generate` should NOT be added to `__init__.py`. So we use public imports where possible and keep only `generate` as a private import.

| Current (lines 36-37) | Fix |
|---|---|
| `from pytanga.codegen._cache import cache_root, lookup` | `from pytanga.codegen import cache_root, lookup` |
| `from pytanga.codegen._generator import generate, module_name` | `from pytanga.codegen import module_name` (on line 7); `from pytanga.codegen._generator import generate` (keep private, add comment) |

Also:
- Line 268: `from pytanga._cache import invalidate, clear` — this path is wrong (no `pytanga._cache` module). Should be `from pytanga.codegen import invalidate, clear`.

---

## Edge Cases Verified

- `alg.nvp(...)` — ✅ exists on `Algebra` (confirmed in `_algebra.py`)
- `alg.all_blades()` — ✅ exists on `Algebra`
- `product="op"` / `product="gp"` — ✅ works at runtime since `EProduct` is a `StrEnum`; style cleanup optional
- `alg({...})` — ✅ creates MV from dict, valid

---

## Implementation Order

1. Group 1: bulk fix `from pytanga.mv import MV` (8 files, simple find-replace)
2. Group 2: fix `from pytanga.mv_utils` (2 files)
3. Group 3: fix `solver_point_line_p3.py` (3 import fixes + minor style)
4. Group 4: fix `solver_rotor_estimation.py` (`alg.random_mv` → `random_mv(alg, ...)`)
5. Group 5: fix `binding_demo.py` (3 import fixes: public codegen API, keep `generate` private, fix `_cache` path)