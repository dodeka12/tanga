# Phase 4 — Solver Updates

← [Back to Overview](./overview.md)

> **Always consider the developer docs** under `docs/dev/` when implementing  
> any step in this plan.

## Goal

Update `MVSolver` in `solver.py` to use the new naming conventions
(`a_mask`, `b_mask`, `c_mask`), return `MVProductMatrix` from product-matrix
methods, support multi-MV `to_matrix`, and accept optional `a_mask` in
`product_matrix_array`.

---

## Current State

`MVSolver` methods currently use `col_mask` / `row_mask` naming, return
`MVMatrix` from `product_matrix`, return `np.ndarray` from
`product_matrix_array`, and `to_matrix` only accepts a single MV.

---

## Steps

### Step 4.1 — Update `product_blade_mask`

**File:** `py/pytanga/solver.py`

- Rename `col_mask` → `b_mask`.
- Internally extract `a_mask` from `a` via `BladeMask.from_mv(self._alg, mv_a)`.
- Call the new mask-based C++ binding (from Phase 1):
  `mod.product_blade_mask_gp_a(a_ids, b_ids, left, complete)`.
- Returned mask is called `c_mask` in the docstring.

```python
def product_blade_mask(
    self,
    a: MVLike,
    b_mask: BladeMask,
    *,
    product: Literal["gp", "ip", "op"] = "gp",
    left: bool = True,
    complete: bool = False,
) -> BladeMask:
    """Predict the output blade mask (c_mask) of A ∘ B.

    Parameters
    ----------
    a : MVLike
        The fixed-coefficient multivector A.
    b_mask : BladeMask
        Blade mask of the unknown X (B).
    product : 'gp' | 'ip' | 'op'
    left : bool
        True = A ∘ B → C; False = B ∘ A → C.
    complete : bool
        When True, iterate to fixed-point sub-algebra closure.

    Returns
    -------
    BladeMask
        c_mask — the blade mask of the result C.
    """
    assert b_mask.algebra is self._alg
    mv = self._as_mv(a)
    a_mask = BladeMask.from_mv(self._alg, mv)
    _, _, _, mask_fn = self._dispatch(product)
    # mask_fn is e.g. "product_blade_mask_gp" — append "_a" for mask-based
    raw_ids = getattr(self._alg._mod, mask_fn + "_a")(a_mask.ids, b_mask.ids, left, complete)
    return BladeMask(self._alg, raw_ids)
```

### Step 4.2 — Update `to_matrix`

`to_matrix` now accepts either a single `MVLike` or a `list[MVLike]`.

- For a **single MV**: calls existing C++ `to_matrix` (returns column vector
  of shape `(n, 1)`).
- For a **list of MVs**: iterates in Python, stacking columns into an
  `(n, n_mvs)` matrix.

```python
def to_matrix(self, a: MVLike | list[MVLike], mask: BladeMask) -> MVMatrix:
    """Extract coefficients of *a* into an MVMatrix.

    Parameters
    ----------
    a : MVLike | list[MVLike]
        Single multivector or list of multivectors.
    mask : BladeMask
        Row index space.

    Returns
    -------
    MVMatrix
        Shape ``(len(mask), n_mvs)``.
    """
    assert mask.algebra is self._alg
    from .mv import MV as _MV
    if isinstance(a, list):
        mvs = [self._as_mv(x) for x in a]
        n = len(mask)
        cols = [self._alg._mod.to_matrix(mv._impl, mask.ids) for mv in mvs]
        arr = np.hstack(cols)         # (n, n_mvs)
        return MVMatrix(data=arr, row_mask=mask)
    else:
        mv = self._as_mv(a)
        arr = self._alg._mod.to_matrix(mv._impl, mask.ids)
        return MVMatrix(data=arr, row_mask=mask)
```

### Step 4.3 — Update `from_matrix`

Takes an `MVMatrix` (may have multiple columns).  Returns a single `MV` when
`m.is_single`, otherwise a `list[MV]`.

```python
def from_matrix(self, m: MVMatrix) -> "MV | list[MV]":
    """Reconstruct MV(s) from an MVMatrix.

    Returns a single MV when ``m.is_single``, otherwise a list of MVs.
    """
    assert m.algebra is self._alg
    from .mv import MV
    if m.is_single:
        impl = self._alg._mod.from_matrix(m.data, m.row_mask.ids)
        return MV(impl, self._alg)
    else:
        mvs: list[MV] = []
        for col_idx in range(m.n_cols):
            col_data = m.data[:, col_idx:col_idx+1]
            impl = self._alg._mod.from_matrix(col_data, m.row_mask.ids)
            mvs.append(MV(impl, self._alg))
        return mvs
```

### Step 4.4 — Update `product_matrix`

- Rename `col_mask` → `b_mask`, `row_mask` → `c_mask`.
- `a_mask` stays `a_mask` (already matches the new convention).
- When `a_mask` is None: compute it from `a` via `BladeMask.from_mv`.
- Build **3‑D tensor** by iterating over `a_mask` blades, calling the
  existing C++ 3-mask `product_matrix_*_masked` for each blade.
- Return `MVProductMatrix`.

```python
def product_matrix(
    self,
    a: MVLike,
    b_mask: BladeMask,
    c_mask: BladeMask,
    *,
    product: Literal["gp", "ip", "op"] = "gp",
    left: bool = True,
    a_mask: BladeMask | None = None,
) -> MVProductMatrix:
    """Build the product matrix M such that M · vec(B) = vec(C).

    Returns a 3‑D MVProductMatrix of shape (|a_mask|, |c_mask|, |b_mask|).
    """
    assert b_mask.algebra is self._alg
    assert c_mask.algebra is self._alg
    mv = self._as_mv(a)
    if a_mask is None:
        a_mask = BladeMask.from_mv(self._alg, mv)

    _, fn3, _, _ = self._dispatch(product)
    na, nc, nb = len(a_mask), len(c_mask), len(b_mask)
    arr = np.zeros((na, nc, nb), dtype=np.float64 if self._alg.dtype.startswith("float") else np.int64)

    for i, aid in enumerate(a_mask.ids):
        single_mask = BladeMask(self._alg, [aid])
        mat2d = self._alg._mod.__getattr__(fn3)(
            mv._impl, single_mask.ids, b_mask.ids, c_mask.ids, left
        )
        arr[i] = mat2d

    return MVProductMatrix(data=arr, a_mask=a_mask, b_mask=b_mask, c_mask=c_mask)
```

> **Alternative (simpler, likely faster):** If the C++ `_EvalProductMatrix`
> 3‑mask overload is already tensor-ready (it produces a stacked 2‑D matrix),
> build the 3‑D array by reshaping the stacked 2‑D output to `(|a_mask|, |c_mask|, |b_mask|)`.
> The implementer should measure both approaches.

### Step 4.5 — Update `product_matrix_array`

- Accept optional `a_mask`.  When not given, auto-compute via
  `BladeMask.from_array(mvs)`.
- Rename `col_mask` → `b_mask`, `row_mask` → `c_mask`.
- Iterate MVs, call `product_matrix` for each, stack slices into a 3‑D tensor.
- Return `MVProductMatrix`.

```python
def product_matrix_array(
    self,
    mvs: list[MVLike],
    b_mask: BladeMask,
    c_mask: BladeMask,
    *,
    product: Literal["gp", "ip", "op"] = "gp",
    left: bool = True,
    a_mask: BladeMask | None = None,
) -> MVProductMatrix:
    """Build a stacked product matrix from a list of multivectors.

    Returns a 3‑D MVProductMatrix of shape (|a_mask|, |c_mask|, |b_mask|).
    """
    assert b_mask.algebra is self._alg
    assert c_mask.algebra is self._alg
    impls = [self._as_mv(mv) for mv in mvs]
    if a_mask is None:
        a_mask = BladeMask.from_array(self._alg, impls)

    na, nc, nb = len(a_mask), len(c_mask), len(b_mask)
    arr = np.zeros((na, nc, nb), dtype=np.float64 if self._alg.dtype.startswith("float") else np.int64)

    _, fn3, _, _ = self._dispatch(product)
    for i, mv_impl in enumerate(impls):
        # Use the a_mask entry for this MV, or fall back to its own blade mask
        aid = a_mask.ids[i] if i < len(a_mask) else None
        if aid is not None:
            single_mask = BladeMask(self._alg, [aid])
            mat2d = self._alg._mod.__getattr__(fn3)(
                mv_impl._impl, single_mask.ids, b_mask.ids, c_mask.ids, left
            )
        else:
            # Fall back: use the MV's own blade mask
            local_a = BladeMask.from_mv(self._alg, mv_impl)
            mat2d = self._alg._mod.__getattr__(fn3)(
                mv_impl._impl, local_a.ids, b_mask.ids, c_mask.ids, left
            )
        arr[i] = mat2d

    return MVProductMatrix(data=arr, a_mask=a_mask, b_mask=b_mask, c_mask=c_mask)
```

> **Note:** The `a_mask` from `from_array` is the *union* of all individual
> blade sets.  The `i`-th MV may not contain all blades in `a_mask`.  The
> loop above uses `a_mask.ids[i]` if `|a_mask| == len(mvs)`; otherwise it
> falls back to each MV's own blade mask.  The implementer should decide on
> the exact contract and handle edge cases consistently.

### Step 4.6 — Update `solve`, `solve_lsq`, `solve_mod`

These high-level methods create temporary masks internally.  Update:

- Rename local variables: `col_mask` → `b_mask`, `row_mask` → `c_mask`.
- `product_matrix` now returns `MVProductMatrix` — access `.data` for numpy
  operations.  For a single-MV call, `M.data` has shape `(1, |c_mask|, |b_mask|)`,
  so slice `M.data[0]` to get the 2‑D `(|c_mask|, |b_mask|)` matrix.
- `to_matrix` still returns `MVMatrix` (column vector).
- `from_matrix` still returns an `MV` (single column).
- Keep public API unchanged (they return `MV`).

Example update for `solve`:

```python
def solve(self, a, y, *, product="gp", left=True):
    # ...
    M = self.product_matrix(mv_a, b_mask, c_mask, product=product, left=left)
    M2d = M.data[0]  # (|c_mask|, |b_mask|)
    b = self.to_matrix(mv_y, c_mask)
    # b.data is (|c_mask|, 1)
    x_arr = np.linalg.solve(M2d, b.data)
    return self.from_matrix(MVMatrix(x_arr, b_mask))
```

Apply similar changes to `solve_lsq` and `solve_mod`.

---

## Verification

After completing all steps:

1. Existing solver tests still pass with updated parameter names.
2. `product_matrix` returns a 3‑D `MVProductMatrix`.
3. `product_matrix_array` with/without explicit `a_mask` works correctly.
4. `to_matrix` with a list of MVs returns multi-column `MVMatrix`.
5. `from_matrix` with multi-column `MVMatrix` returns `list[MV]`.
6. High-level `solve` still returns correct results.

---

## Files Touched

| File | Action |
|---|---|
| `py/pytanga/solver.py` | Rewrite all methods — renames, return types, new logic |

---

## Dependencies

- **Requires:** Phase 1 (mask-based C++ bindings), Phase 2 (new classes), Phase 3 (`from_array`).
- **Downstream:** Phase 5 (docs), Phase 6 (tests).