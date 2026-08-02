# Phase 2 — MVMatrix / MVProductMatrix Refactor

← [Back to Overview](./overview.md)

> **Always consider the developer docs** under `docs/dev/` when implementing  
> any step in this plan.

## Goal

Split the current dual-purpose `MVMatrix` into two clean classes:

- **`MVMatrix`** — a 2‑D array holding one or more multivectors as columns,
  rows labelled by a `BladeMask`.  No column mask.
- **`MVProductMatrix`** — a 3‑D tensor `(|a_mask|, |c_mask|, |b_mask|)`
  encoding one product matrix per element of `a_mask`.  Axes labelled by
  `a_mask`, `b_mask`, `c_mask`.

This is a pure-Python change; no C++ involved.

---

## Current State

```python
@dataclass
class MVMatrix:
    data: np.ndarray
    row_mask: BladeMask
    col_mask: BladeMask | None = None
```

`MVMatrix` serves dual roles:
- Single column vector (empty `col_mask`)
- Product matrix (both masks populated)

---

## Steps

### Step 2.1 — Redesign `MVMatrix` for column data

**File:** `py/pytanga/mv_matrix.py`

Replace the existing `MVMatrix` implementation with the new design:

```python
@dataclass
class MVMatrix:
    """A numpy matrix whose rows are labelled by a blade mask.

    Each column stores the coefficients of one multivector, all ordered
    by the same ``row_mask``.  For a single multivector this is a column
    vector (``n_cols == 1``); for a list of MVs this is an ``(n_rows, n_mvs)``
    matrix.

    Parameters
    ----------
    data : np.ndarray
        Shape ``(len(row_mask), n_cols)``.
    row_mask : BladeMask
        Ordered blade ids labelling each row.
    """

    data: np.ndarray
    row_mask: BladeMask

    def __post_init__(self) -> None:
        if self.data.ndim != 2:
            raise ValueError(f"MVMatrix.data must be 2-D, got ndim={self.data.ndim}")
        if len(self.row_mask) != self.data.shape[0]:
            raise ValueError(
                f"len(row_mask)={len(self.row_mask)} does not match "
                f"data.shape[0]={self.data.shape[0]}"
            )

    @property
    def shape(self) -> tuple[int, ...]:
        return self.data.shape

    @property
    def n_cols(self) -> int:
        """Number of multivectors stored (columns)."""
        return self.data.shape[1]

    @property
    def is_single(self) -> bool:
        """True when exactly one multivector is stored."""
        return self.data.shape[1] == 1

    @property
    def algebra(self) -> "Algebra":
        return self.row_mask._alg
```

**Key changes from the current `MVMatrix`:**
- `col_mask` is **removed** entirely.
- `is_column_vector` → `is_single`.
- `n_cols` property replaces `len(col_mask)` for column count.
- No `__post_init__` validation against `col_mask`.

### Step 2.2 — Create `MVProductMatrix` (3‑D tensor)

**File:** `py/pytanga/mv_matrix.py`

Add the new class **after** `MVMatrix` in the same file:

```python
@dataclass
class MVProductMatrix:
    """A 3-D tensor encoding one product matrix per blade of a_mask.

    Each slice ``data[i, :, :]`` is the ``(|c_mask| x |b_mask|)`` product
    matrix for blade ``a_mask[i]``.

    A standard matrix product with an MVMatrix column vector V contracts
    the last axis and broadcasts over the first::

        M.data @ V.data   ->  (|a_mask|, |c_mask|, 1)
        .squeeze(-1).T     ->  (|c_mask|, |a_mask|)   (MVMatrix layout)

    Parameters
    ----------
    data : np.ndarray
        Shape ``(|a_mask|, |c_mask|, |b_mask|)``.  3-D tensor.
    a_mask : BladeMask
        First  axis — the blade subspace of A (or list of MVs).
    b_mask : BladeMask
        Last   axis — the subspace of the unknown X.
    c_mask : BladeMask
        Middle axis — the output subspace.
    """

    data: np.ndarray
    a_mask: BladeMask
    b_mask: BladeMask
    c_mask: BladeMask

    def __post_init__(self) -> None:
        if self.data.ndim != 3:
            raise ValueError(
                f"MVProductMatrix.data must be 3-D, got ndim={self.data.ndim}"
            )
        na = len(self.a_mask)
        nc = len(self.c_mask)
        nb = len(self.b_mask)
        if self.data.shape != (na, nc, nb):
            raise ValueError(
                f"data.shape={self.data.shape} does not match "
                f"a_mask(|a_mask|={na}) x c_mask(|c_mask|={nc}) x b_mask(|b_mask|={nb})"
            )
        if self.b_mask.algebra is not self.c_mask.algebra:
            raise ValueError("b_mask and c_mask belong to different algebras")

    @property
    def n_mvs(self) -> int:
        """Number of multivectors encoded in this tensor (= |a_mask|)."""
        return len(self.a_mask)

    @property
    def shape(self) -> tuple[int, ...]:
        return self.data.shape

    @property
    def algebra(self) -> "Algebra":
        return self.b_mask.algebra
```

**Tensor layout rationale:**

| Axis | Mask | Meaning |
|---|---|---|
| 0 | `a_mask` | Enumerates blades of A (or MVs in the list) |
| 1 | `c_mask` | Output row subspace for each product |
| 2 | `b_mask` | Input column subspace of unknown X |

A `matmul` with a column vector of shape `(|b_mask|, 1)` broadcasts over
axis 0, producing `(|a_mask|, |c_mask|, 1)`.

### Step 2.3 — Update `__init__.py` exports

**File:** `py/pytanga/__init__.py`

Add `MVProductMatrix` to the public exports alongside `MVMatrix`:

```python
from ._mv_matrix import MVMatrix, MVProductMatrix
```

Ensure both names are in `__all__` if the module uses one.

---

## Verification

After completing all steps:

1. Import both classes:
   ```python
   from pytanga import MVMatrix, MVProductMatrix
   ```

2. Construct an `MVMatrix` (no `col_mask` parameter):
   ```python
   import numpy as np
   alg = pytanga.Algebra(3, 0)
   mask = pytanga.BladeMask.full(alg)
   m = MVMatrix(data=np.zeros((len(mask), 1)), row_mask=mask)
   assert m.is_single
   assert m.n_cols == 1
   assert m.algebra is alg
   ```

3. Construct an `MVProductMatrix` (3‑D tensor with 3 masks):
   ```python
   a_mask = pytanga.BladeMask(alg, [1, 2])   # e1, e2
   b_mask = mask
   c_mask = mask
   pm = MVProductMatrix(
       data=np.zeros((2, 8, 8)),
       a_mask=a_mask,
       b_mask=b_mask,
       c_mask=c_mask,
   )
   assert pm.n_mvs == 2
   assert pm.shape == (2, 8, 8)
   ```

4. Verify validation:
   - Passing 2‑D data raises `ValueError` ("must be 3‑D").
   - Mismatched shape raises `ValueError`.
   - Mismatched algebras on `b_mask`/`c_mask` raises `ValueError`.

---

## Files Touched

| File | Action |
|---|---|
| `py/pytanga/mv_matrix.py` | Rewrite `MVMatrix`, add `MVProductMatrix` |
| `py/pytanga/__init__.py` | Export `MVProductMatrix` |

---

## Upstream Dependencies

- None (pure Python, can run in parallel with Phase 1).
- **Downstream:** Phase 4 (`solver.py`) imports both classes.