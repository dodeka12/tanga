# Solver Restructure Plan

**Goal:** Break the monolithic `py/pytanga/solver.py` (~600 lines) into a `py/pytanga/solver/` submodule with multiple focused files, each holding free functions that take `alg: Algebra` as first parameter. Remove the `MVSolver` class entirely, remove `alg.solver` property, and adapt all consumers.

---

## 1. New File Structure

```
py/pytanga/solver/
├── __init__.py            # Empty (no re-exports; individuals import from specific files)
├── blade_masks.py         # inverse_blade_mask, product_blade_mask
├── matrix_product.py      # product_matrix, product_matrix_rev, product_matrix_conj
├── matrix_convert.py      # to_matrix, from_matrix
├── solve.py               # solve, solve_lsq, solve_mod
├── _dispatch.py           # (private) C++ binding dispatch helpers
├── _coerce.py             # (private) _as_mv, MVLike type alias
```

| File | Content | Public Signature |
|------|---------|------------------|
| `blade_masks.py` | `inverse_blade_mask`, `product_blade_mask` | `def inverse_blade_mask(alg, a_mask, c_mask, *, product, left) -> BladeMask` |
| `matrix_product.py` | `product_matrix`, `product_matrix_rev`, `product_matrix_conj` | `def product_matrix(alg, a, *, a_mask, b_mask, c_mask, product, left, left_inv, right_inv) -> MVProductMatrix` |
| `matrix_convert.py` | `to_matrix`, `from_matrix` | `def to_matrix(alg, a, mask) -> MVMatrix` |
| `solve.py` | `solve`, `solve_lsq`, `solve_mod` | `def solve(alg, a, c, *, a_mask, b_mask, c_mask, product, left) -> MV` |
| `_dispatch.py` | private dispatch methods | `_dispatch_product_matrix_masked(alg, ...)` etc. |
| `_coerce.py` | `_as_mv`, `MVLike` | (private) |

### Key Design Decisions

1. **Every public function takes `alg: Algebra` as its first positional parameter.** This replaces `self._alg` throughout.
2. **No `MVSolver` class exists.** Users call free functions directly:
   ```python
   from pytanga.solver.solve import solve
   X = solve(alg, A, C)
   ```
3. **`solver/__init__.py` is empty.** Users import from the specific submodule files they need. No bulk re-exports.
4. **Files with public API do NOT start with underscore.** Files with private internals (`_dispatch`, `_coerce`) do.
5. **`alg.solver` property is removed from `algebra.py`.**

### Internal Dependencies

```
solver/blade_masks.py     → Algebra, BladeMask, EProduct (no solver internals)
solver/_coerce.py          → Algebra, MV (no solver internals)
solver/_dispatch.py        → Algebra, EProduct, EInv (no solver internals)
solver/matrix_product.py   → blade_masks, _dispatch, _coerce, MVProductMatrix
solver/matrix_convert.py   → Algebra, BladeMask, MVMatrix, _coerce
solver/solve.py            → product_matrix, matrix_convert, blade_masks, _coerce
```

---

## 2. Changes to Existing Files

### 2.1 `py/pytanga/__init__.py`

Delete `from .solver import MVSolver` and `"MVSolver"` from `__all__`.

**Before:**
```python
from .solver import MVSolver
__all__ = [..., "MVSolver", ...]
```

**After:** those two lines are removed.

---

### 2.2 `py/pytanga/algebra.py`

Delete the `solver` property:

```python
# REMOVE THIS ENTIRELY:
@property
def solver(self) -> "MVSolver":
    from .solver import MVSolver
    return MVSolver(self)
```

Also remove the `__slots__` entry `"_solver"` and the initialization `self._solver: MVSolver | None = None`.

---

### 2.3 `py/pytanga/solver.py` (existing)

Delete this file. It is replaced by the `solver/` submodule.

---

## 3. Test Adaptations

### 3.1 `py/tests/conftest.py`

Replace:
```python
from pytanga import MVSolver

@pytest.fixture(scope="module")
def slv_float(alg_float):
    return MVSolver(alg_float)

@pytest.fixture(scope="module")
def slv_int(alg_int):
    return MVSolver(alg_int)
```

With passthrough fixtures that just return the algebra (or delete them and have tests import functions directly):

```python
# Option A: algebra-only fixtures (recommended — tests use free functions)
# Delete slv_float and slv_int fixtures entirely.
# Tests that need them now call `solve(alg_float, ...)` directly.
```

Or minimal shims:
```python
# Option B: keep fixture names as aliases to algebra (less churn)
@pytest.fixture(scope="module")
def slv_float(alg_float):
    """Alias — free functions now take alg as first arg."""
    return alg_float
```

Recommendation: **Delete the `slv_float`/`slv_int` fixtures** and update each test to import the functions it needs. This is explicit and avoids confusion.

### 3.2 Test files using `MVSolver(...)` or `.solver`

| File | Current pattern | New pattern |
|------|----------------|-------------|
| `test_solve_float.py` | `from pytanga.solver import MVSolver`<br>`slv = MVSolver(alg)`<br>`slv.solve(A, C)` | `from pytanga.solver.solve import solve, solve_lsq`<br>`solve(alg, A, C)` |
| `test_solve_mod.py` | `from pytanga.solver import MVSolver`<br>`slv = MVSolver(alg)`<br>`slv.solve_mod(A, C, mod)` | `from pytanga.solver.solve import solve_mod`<br>`solve_mod(alg, A, C, 97)` |
| `test_least_squares.py` | `from pytanga.solver import MVSolver`<br>`slv = MVSolver(alg)`<br>`slv.solve_lsq(A, C)` | `from pytanga.solver.solve import solve_lsq`<br>`solve_lsq(alg, A, C)` |
| `test_blade_mask.py` | `from pytanga.solver import MVSolver`<br>`solver = MVSolver(alg)`<br>`solver.inverse_blade_mask(...)` | `from pytanga.solver.blade_masks import inverse_blade_mask, product_blade_mask`<br>`inverse_blade_mask(alg, ...)` |
| `test_product_matrix.py` | `from pytanga.solver import MVSolver`<br>`slv = MVSolver(alg)`<br>`slv.product_matrix(...)` | `from pytanga.solver.product_matrix import product_matrix`<br>`product_matrix(alg, ...)` |
| `test_product_matrix_rev_conj.py` | Same pattern | `from pytanga.solver.product_matrix import product_matrix_rev, product_matrix_conj` |
| `test_product_matrix_einv.py` | Same pattern | Same as above + `product_matrix` |
| `test_mvproductmatrix.py` | Same pattern | `from pytanga.solver.product_matrix import product_matrix` |
| `test_matrix_conversion.py` | `from pytanga.solver import MVSolver`<br>`slv = MVSolver(alg)`<br>`slv.to_matrix(...)` | `from pytanga.solver.matrix_convert import to_matrix, from_matrix`<br>`to_matrix(alg, ...)` |
| `test_solver_property.py` | `from pytanga import MVSolver`<br>`assert isinstance(slv, MVSolver)` | Delete this test (no more MVSolver class to check) |
| `test_mvlike_coercion.py` | `from pytanga.solver import MVLike, MVSolver` | `from pytanga.solver._coerce import MVLike`<br>(_as_mv is private, tested indirectly) |
| `test_modular.py` | `from pytanga.solver import MVSolver`<br>`slv = MVSolver(alg)` | `from pytanga.solver.solve import solve_mod` |

**Pattern for each test file update:**
1. Replace `from pytanga.solver import MVSolver` with specific function imports.
2. Replace `slv = MVSolver(alg)` with nothing (or reuse `alg` directly).
3. Replace `slv.method(...)` with `function(alg, ...)`.
4. If a test fixture `slv_float`/`slv_int` was used, replace with `alg_float`/`alg_int` fixture.

---

## 4. Example Adaptations

### 4.1 `py/examples/solver_basics_01.py`

**Before:**
```python
from pytanga import MV, Algebra, EProduct, MVMatrix, MVSolver
alg = Algebra(3, 0, "float64")
slv: MVSolver = alg.solver
...
M = slv.product_matrix(A, product=EProduct.GP)
B1 = slv.solve(A, 1.0)
```

**After:**
```python
from pytanga import MV, Algebra, EProduct, MVMatrix
from pytanga.solver.product_matrix import product_matrix
from pytanga.solver.solve import solve
from pytanga.solver.matrix_convert import to_matrix, from_matrix
alg = Algebra(3, 0, "float64")
...
M = product_matrix(alg, A, product=EProduct.GP)
B1 = solve(alg, A, 1.0)
```

### 4.2 `py/examples/solver_basics_02.py`

Same pattern — replace `slv.solve(...)` with `solve(alg, ...)`, `slv.product_matrix(...)` with `product_matrix(alg, ...)`, `slv.to_matrix(...)` with `to_matrix(alg, ...)`.

### 4.3 `py/examples/solver_basics_03.py`

Same pattern. Uses `slv.solve(...)`, `slv.solve_lsq(...)` → `solve(alg, ...)`, `solve_lsq(alg, ...)`.

### 4.4 `py/examples/solver_line_fitting_p2.py`

Uses `slv.product_matrix(...)`, `slv.to_matrix(...)`, `slv.from_matrix(...)`, `slv_int.solve_mod(...)`.
→ `product_matrix(alg, ...)`, `to_matrix(alg, ...)`, `from_matrix(alg, ...)`, `solve_mod(alg_int, ...)`.

### 4.5 `py/examples/solver_point_line_p3.py`

Uses `slv.product_blade_mask(...)`, `slv.product_matrix(...)`, `slv.to_matrix(...)`.
→ `product_blade_mask(alg, ...)`, `product_matrix(alg, ...)`, `to_matrix(alg, ...)`.

### 4.6 `py/examples/solver_rotor_estimation.py`

Uses `slv.product_matrix(...)`, `slv.solve_lsq(...)`, `slv.from_matrix(...)`.
→ `product_matrix(alg, ...)`, `solve_lsq(alg, ...)`, `from_matrix(alg, ...)`.

---

## 5. Documentation Updates

### 5.1 `docs/py/solver.md`

Update to document free-function API. Document the module structure:

```markdown
# pytanga.solver — Equation-Solving Machinery

The `pytanga.solver` submodule provides free functions for building product
matrices, predicting blade masks, and solving multivector equations. All
public functions take an `Algebra` instance as their first argument.

## Submodule Structure

| Module | Functions |
|--------|-----------|
| `pytanga.solver.blade_masks` | `inverse_blade_mask`, `product_blade_mask` |
| `pytanga.solver.product_matrix` | `product_matrix`, `product_matrix_rev`, `product_matrix_conj` |
| `pytanga.solver.matrix_convert` | `to_matrix`, `from_matrix` |
| `pytanga.solver.solve` | `solve`, `solve_lsq`, `solve_mod` |

## Quick Start

```python
import pytanga as pt
from pytanga.solver.solve import solve

alg = pt.Algebra("e3")
A = alg.multivector("e1 + e2")
C = alg.multivector("2.0")
X = solve(alg, A, C)
print(X)
```
```

---

## 6. Implementation Order

1. **Create `py/pytanga/solver/` directory** with empty `__init__.py`
2. **Create `_coerce.py`** — move `MVLike` and `_as_mv` from old `solver.py`
3. **Create `_dispatch.py`** — move all `_dispatch_*` methods
4. **Create `blade_masks.py`** — move `inverse_blade_mask`, `product_blade_mask`
5. **Create `matrix_product.py`** — move `product_matrix`, `product_matrix_rev`, `product_matrix_conj`, and `product_matrix_array` (if present)
6. **Create `matrix_convert.py`** — move `to_matrix`, `from_matrix`
7. **Create `solve.py`** — move `solve`, `solve_lsq`, `solve_mod`
8. **Update `algebra.py`** — remove `solver` property and `_solver` slot
9. **Update `__init__.py`** — remove MVSolver export
10. **Delete `py/pytanga/solver.py`** — old file
11. **Update all test files** (see section 3)
12. **Update all example files** (see section 4)
13. **Update `docs/py/solver.md`** (see section 5)
14. **Run test suite** — verify everything passes