# Phase 3 — MVSolver Class

← [Back to Overview](./overview.md)

> **Always consider the developer docs** under `docs/dev/` when implementing any step in this plan.  
> In particular: the [Python Coding Style Guide](../../../docs/dev/guides/py-coding-style-guide.md).  
> Also review any relevant architecture docs, use-case examples, and best practice documentation found there.

## Goal

Implement `MVSolver` in `py/pytanga/solver.py`.  The class is stateless (holds
only the `Algebra` reference) and exposes three tiers of API:

1. **Blade-mask utilities** — predict and construct blade-id lists.
2. **Matrix primitives** — convert between `MV` and `MVMatrix`, and build
   product matrices.
3. **High-level solvers** — `solve`, `solve_lsq`, `solve_mod` that derive masks
   automatically and return `MV` directly.

By the end of this phase `MVSolver` is fully functional when constructed
directly from an `Algebra` instance.

---

## Steps

### 3.1 — Scaffold `MVSolver` and blade-mask utilities ✓

Add the `MVSolver` class to `py/pytanga/solver.py`.  This file contains **only**
`MVSolver` — `BladeMask` lives in `blade_mask.py` and `MVMatrix` in
`mv_matrix.py` (Phase 1).  Import them at the top of `solver.py`:

```python
from __future__ import annotations
from typing import TYPE_CHECKING, Literal, Union
import numpy as np
from ._blade_mask import BladeMask
from ._mv_matrix import MVMatrix
if TYPE_CHECKING:
    from .algebra import Algebra
    from .mv import MV

# Convenience union: any method that accepts MV also accepts a scalar or
# a string expression, which is coerced to MV via Algebra.multivector().
MVLike = Union["MV", float, int, str]
```

```python
class MVSolver:
    def __init__(self, alg: "Algebra") -> None: ...

    def _as_mv(self, x: MVLike) -> "MV":
        """Coerce a scalar or string to MV; return MV unchanged."""
        from .mv import MV as _MV
        if isinstance(x, _MV):
            return x
        return self._alg.multivector(x)
```

Every public method that accepts an `MVLike` argument calls `self._as_mv()`
as its first act, so the rest of the implementation always works with a true
`MV` instance.  This avoids repeating the guard in every method body.

Implement the blade-mask methods:

```python
def blade_mask(self, a: MVLike, only_nonzero: bool = True) -> BladeMask
```
Coerces `a` via `_as_mv`, then returns `BladeMask.from_mv(self._alg, a, only_nonzero)`.

```python
def product_blade_mask(self, a: MVLike, col_mask: BladeMask, *,
                       product: Literal['gp', 'ip', 'op'] = 'gp',
                       left: bool = True,
                       complete: bool = False) -> BladeMask
```
Asserts `col_mask.algebra is self._alg`.  Dispatches on `product` to
`self._alg._mod.product_blade_mask_gp/ip/op(a._impl, col_mask.ids, left, complete)`.
Returns `BladeMask(self._alg, result_ids)`.  Still add a runtime `ValueError`
for the exhausted-match case so errors surface if the annotation is bypassed.

`BladeMask.from_str` replaces the former `blade_mask_from_str` method.
String-to-mask conversion now lives on `BladeMask` itself
(`BladeMask.from_str(self._alg, s)`) — no solver method needed.

**Tests:** Verify `blade_mask(a)` returns a `BladeMask` with `.algebra is alg`
and `.ids` matching the expected blade id list.  Verify `product_blade_mask`
asserts when passed a mask from a different algebra.

### 3.2 — Matrix conversion methods ✓

```python
def to_matrix(self, a: MVLike, mask: BladeMask) -> MVMatrix
```
Asserts `mask.algebra is self._alg`.  Calls
`self._alg._mod.to_matrix(a._impl, mask.ids)` → numpy array of shape `(n, 1)`.
Returns `MVMatrix(data=arr, row_mask=mask)` (col_mask defaults to empty).

```python
def from_matrix(self, m: MVMatrix) -> MV
```
Asserts `m.algebra is self._alg`.  Raises `ValueError` if not a column vector.
Calls `self._alg._mod.from_matrix(m.data, m.row_mask.ids)` → `DynMV`.
Wraps in `MV(impl, self._alg)`.

**Tests:** Round-trip `to_matrix` → `from_matrix` for a known MV and verify
the result matches via `mv.to_dict()`. Verify `from_matrix` on a non-column
`MVMatrix` raises `ValueError`. Verify cross-algebra assert fires.

### 3.3 — Product-matrix construction methods ✓

```python
def product_matrix(self, a: MVLike,
                   col_mask: BladeMask,
                   row_mask: BladeMask, *,
                   product: Literal['gp', 'ip', 'op'] = 'gp',
                   left: bool = True,
                   a_mask: BladeMask | None = None) -> MVMatrix
```
Asserts both masks belong to `self._alg`.
When `a_mask` is `None`, calls
`product_matrix_gp/ip/op(a._impl, col_mask.ids, row_mask.ids, left)`.
When `a_mask` is provided, calls
`product_matrix_gp/ip/op_masked(a._impl, a_mask.ids, col_mask.ids, row_mask.ids, left)`.
Returns `MVMatrix(data=arr, row_mask=row_mask, col_mask=col_mask)`.

```python
def product_matrix_array(self, mvs: list[MVLike],
                          col_mask: BladeMask,
                          row_mask: BladeMask, *,
                          product: Literal['gp', 'ip', 'op'] = 'gp',
                          left: bool = True) -> MVMatrix
```
Each element of `mvs` is coerced via `_as_mv` before being passed to C++.
The stacked matrix has `len(mvs) * len(row_mask)` rows; the returned
`MVMatrix` uses a `row_mask` that is the union of `row_mask` repeated
`len(mvs)` times — in practice callers should treat it as a stacked block
matrix and split manually. `col_mask` labels the columns as normal.

**Tests:** For A = `1·e1 - 2·e2` in G(3,0), verify `product_matrix` returns
an `MVMatrix` whose `.data` matches expected values and whose
`.row_mask.ids` and `.col_mask.ids` are correct.

### 3.4 — High-level float solvers ✓

```python
def solve(self, a: MVLike, y: MVLike, *,
          product: Literal['gp', 'ip', 'op'] = 'gp', left: bool = True) -> MV
```
1. `col_mask = self.blade_mask(a)` — blades of A are the unknown subspace.
2. `row_mask = self.product_blade_mask(a, col_mask, product=product, left=left, complete=True)`.
3. Merge any blades of Y not yet in `row_mask`:
   `row_mask = row_mask.union(BladeMask.from_mv(self._alg, y))`.
4. `M = self.product_matrix(a, col_mask, row_mask, product=product, left=left)`.
5. `b = self.to_matrix(y, row_mask)`.
6. Validate `M.data.shape[0] == M.data.shape[1]`; raise `ValueError("System
   is not square — use solve_lsq")` otherwise.
7. `x_arr = np.linalg.solve(M.data, b.data)`.
8. Return `self.from_matrix(MVMatrix(x_arr, col_mask))`.

Raises `numpy.linalg.LinAlgError` (from numpy) if the system is singular;
let it propagate without wrapping.

Only available for float dtypes. Raises `TypeError` for integer dtypes with a
message directing the user to `solve_mod`.

```python
def solve_lsq(self, a: MVLike, y: MVLike, *,
              product: Literal['gp', 'ip', 'op'] = 'gp',
              tol: float = 1e-10) -> MV
```
Same mask derivation as `solve`.  Uses `np.linalg.lstsq(M.data, b.data, rcond=tol)`
and returns `self.from_matrix(MVMatrix(x_arr.reshape(-1,1), col_mask))`.

Only available for float dtypes.

**Tests:** In G(5,0) float64, solve `A * X = Y` for a known invertible A and
verify `A * X ≈ Y` to within 1e-10. Verify that a singular A raises
`LinAlgError`. Verify that calling on an integer algebra raises `TypeError`.

### 3.5 — Modular-integer solver ✓

```python
def solve_mod(self, a: MVLike, y: MVLike, modulus: int, *,
              product: Literal['gp', 'ip', 'op'] = 'gp', left: bool = True) -> MV
```
1. `col_mask = self.blade_mask(a)`.
2. `row_mask = self.product_blade_mask(a, col_mask, product=product, left=left, complete=True)`.
3. Merge Y's blades: `row_mask = row_mask.union(BladeMask.from_mv(self._alg, y))`.
4. Calls `self._alg._mod.solve_mod(a._impl, y._impl, col_mask.ids, row_mask.ids, modulus)` → `DynMV`.
5. Wraps in `MV(impl, self._alg)`.

Only available for integer dtypes. Raises `TypeError` for float dtypes.
Raises `RuntimeError` (propagated from C++) if the system has no unique
solution modulo `modulus`.

**Tests:** In G(3,0) int64, verify `solve_mod(A, scalar_1, modulus)` returns
the modular inverse (cross-check against `alg.inv(A, modulus)`). Verify that
a non-invertible A raises `RuntimeError`.
