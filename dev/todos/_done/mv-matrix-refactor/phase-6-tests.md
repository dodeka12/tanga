# Phase 6 — Test Updates and New Tests

← [Back to Overview](./overview.md)

> **Always consider the developer docs** under `docs/dev/` when implementing  
> any step in this plan.

## Goal

Update the existing solver test suite to reflect the renamed parameters and
new types, and add tests for all new functionality introduced in this
refactor.

---

## Steps

### Step 6.1 — Update existing solver tests

**File:** `py/tests/test_solver.py`

Make these changes throughout the file:

1. **Rename all mask references:**
   - `col_mask` → `b_mask`
   - `row_mask` → `c_mask`

2. **Update `MVMatrix` usages:**
   - Remove all references to `col_mask` attribute.
   - Replace `m.is_column_vector` with `m.is_single`.
   - Use `m.n_cols` to check column count.

3. **Update return-type assertions:**
   - `slv.product_matrix(...)` now returns `MVProductMatrix`, not `MVMatrix`.
   - `slv.product_matrix_array(...)` now returns `MVProductMatrix`, not `np.ndarray`.
   - Access 2‑D matrix via `.data[0]` for single-MV product matrices.

4. **Verify backward compatibility:**
   - All existing tests should pass after the renames (no semantic changes
     to the core solve logic).

### Step 6.2 — Add new tests

Add these new test cases to `py/tests/test_solver.py` (or create a new
`test_mv_matrix_refactor.py` if preferred):

#### Test: `BladeMask.from_array`

```python
def test_blade_mask_from_array():
    alg = pytanga.Algebra(3, 0)
    e1 = alg("e1")
    e2 = alg("e2")
    e12 = alg("e12")

    # Union of distinct blade sets
    mask = pytanga.BladeMask.from_array(alg, [e1, e2])
    assert mask.ids == [1, 2]          # e1, e2

    # Union of overlapping blade sets
    a = alg("e1 + e12")
    b = alg("e2 + e12")
    mask2 = pytanga.BladeMask.from_array(alg, [a, b])
    assert mask2.ids == [1, 2, 3]      # e1, e2, e12

    # Empty list
    mask3 = pytanga.BladeMask.from_array(alg, [])
    assert mask3.ids == []

    # Single MV
    mask4 = pytanga.BladeMask.from_array(alg, [e12])
    assert mask4.ids == [3]            # e12
```

#### Test: `product_matrix_array` with explicit `a_mask`

```python
def test_product_matrix_array_with_a_mask():
    alg = pytanga.Algebra(3, 0)
    slv = alg.solver
    mvs = [alg("e1"), alg("e2"), alg("e3")]
    b_mask = pytanga.BladeMask.full(alg)
    c_mask = pytanga.BladeMask.full(alg)
    a_mask = pytanga.BladeMask(alg, [1, 2, 4])  # e1, e2, e3

    M = slv.product_matrix_array(mvs, b_mask, c_mask, product="gp",
                                  a_mask=a_mask)
    assert isinstance(M, pytanga.MVProductMatrix)
    assert M.a_mask == a_mask
    assert M.b_mask == b_mask
    assert M.c_mask == c_mask
    assert M.shape == (3, len(c_mask), len(b_mask))
```

#### Test: `product_matrix_array` without `a_mask` (auto-compute)

```python
def test_product_matrix_array_auto_a_mask():
    alg = pytanga.Algebra(3, 0)
    slv = alg.solver
    mvs = [alg("e1"), alg("e2"), alg("e12")]
    b_mask = pytanga.BladeMask.full(alg)
    c_mask = pytanga.BladeMask.full(alg)

    M = slv.product_matrix_array(mvs, b_mask, c_mask, product="gp")
    assert isinstance(M, pytanga.MVProductMatrix)
    # Auto-computed a_mask should be union of {e1}, {e2}, {e12}
    assert set(M.a_mask.ids) == {1, 2, 3}
    assert M.n_mvs == 3
```

#### Test: `product_blade_mask` with mask-based path

```python
def test_product_blade_mask_renamed():
    alg = pytanga.Algebra(3, 0)
    slv = alg.solver
    a = alg("e1")
    b_mask = pytanga.BladeMask(alg, [1, 2])   # e1, e2

    c_mask = slv.product_blade_mask(a, b_mask, product="gp")
    # e1 * e1 = scalar, e1 * e2 = e12
    assert 0 in c_mask.ids                    # scalar
    assert 3 in c_mask.ids                    # e12
```

#### Test: `from_matrix` with multi-column `MVMatrix`

```python
def test_from_matrix_multi_column():
    alg = pytanga.Algebra(3, 0)
    slv = alg.solver
    mask = pytanga.BladeMask(alg, [1, 2, 4])  # e1, e2, e3
    data = np.array([[1, 0],
                     [0, 1],
                     [0, 0]], dtype=np.float64)
    m = pytanga.MVMatrix(data=data, row_mask=mask)
    assert m.n_cols == 2
    assert not m.is_single

    result = slv.from_matrix(m)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0].to_dict() == {1: 1.0}
    assert result[1].to_dict() == {2: 1.0}
```

#### Test: `MVProductMatrix` validation

```python
def test_mv_product_matrix_validation():
    alg = pytanga.Algebra(3, 0)
    a_mask = pytanga.BladeMask(alg, [1, 2])
    b_mask = pytanga.BladeMask.full(alg)
    c_mask = pytanga.BladeMask.full(alg)

    # 3‑D shape must match
    with pytest.raises(ValueError):
        pytanga.MVProductMatrix(data=np.zeros((2, 8)),  # 2‑D
                                 a_mask=a_mask, b_mask=b_mask, c_mask=c_mask)

    with pytest.raises(ValueError):
        pytanga.MVProductMatrix(data=np.zeros((3, 8, 8)),  # wrong a-dim
                                 a_mask=a_mask, b_mask=b_mask, c_mask=c_mask)

    with pytest.raises(ValueError):
        pytanga.MVProductMatrix(data=np.zeros((2, 7, 8)),  # wrong c-dim
                                 a_mask=a_mask, b_mask=b_mask, c_mask=c_mask)

    # Mismatched algebras
    alg2 = pytanga.Algebra(4, 0)
    c_mask2 = pytanga.BladeMask.full(alg2)
    with pytest.raises(ValueError):
        pytanga.MVProductMatrix(data=np.zeros((2, 8, 8)),
                                 a_mask=a_mask, b_mask=b_mask, c_mask=c_mask2)
```

#### Test: `to_matrix` with list of MVs

```python
def test_to_matrix_list():
    alg = pytanga.Algebra(3, 0)
    slv = alg.solver
    mvs = [alg("e1"), alg("e2"), alg("3 e3")]
    mask = pytanga.BladeMask(alg, [1, 2, 4])

    mat = slv.to_matrix(mvs, mask)
    assert isinstance(mat, pytanga.MVMatrix)
    assert mat.n_cols == 3
    assert mat.data.shape == (3, 3)
    assert mat.data[0, 0] == 1.0   # e1 coeff
    assert mat.data[1, 1] == 1.0   # e2 coeff
    assert mat.data[2, 2] == 3.0   # e3 coeff
```

### Step 6.3 — Update examples

**Files:** `py/examples/solver_*.py`

- Rename `col_mask` → `b_mask`, `row_mask` → `c_mask` in all solver examples.
- Add `from pytanga import MVProductMatrix` where the return type is checked.
- Update `product_matrix_array` result type references.

---

## Verification

After all phases are complete:

```
uv run python -m pytest py/tests/test_solver.py -v
uv run python -m pytest py/tests/ -v
```

Then run each example script to ensure they still produce correct results:

```
uv run python py/examples/solver_basics.py
uv run python py/examples/solver_line_fitting_p2.py
uv run python py/examples/solver_point_line_p3.py
uv run python py/examples/solver_rotor_estimation.py
```

Then run the smoke test:

```python
import pytanga
import numpy as np

alg = pytanga.Algebra(3, 0)
slv = alg.solver

# BladeMask.from_array
mvs = [alg(f"e{i}") for i in range(1, 4)]
a_mask = pytanga.BladeMask.from_array(alg, mvs)  # union of e1, e2, e3

# product_matrix returns MVProductMatrix
M = slv.product_matrix(alg("e1"), a_mask, pytanga.BladeMask.full(alg))
assert isinstance(M, pytanga.MVProductMatrix)
assert M.b_mask == a_mask
assert M.c_mask == pytanga.BladeMask.full(alg)

# product_matrix_array returns MVProductMatrix (3‑D tensor)
M_arr = slv.product_matrix_array(mvs, a_mask, pytanga.BladeMask.full(alg))
assert isinstance(M_arr, pytanga.MVProductMatrix)
assert M_arr.n_mvs == len(mvs)

# matmul with MVMatrix column vector gives (|a_mask|, |c_mask|, 1)
V = slv.to_matrix(alg("e1"), a_mask)          # (|a_mask|, 1)
C = M_arr.data @ V.data                        # (|a_mask|, |c_mask|, 1)
assert C.shape == (len(a_mask), len(M_arr.c_mask), 1)

# to_matrix with list of MVs → multi-column MVMatrix
mat = slv.to_matrix(mvs, a_mask)
assert mat.n_cols == len(mvs)

# High-level solve still works
X = slv.solve(alg("e1"), 1.0)
check = alg("e1") * X
check.prune()
assert abs(check.scalar - 1.0) < 1e-10

print("All smoke tests passed!")
```

---

## Files Touched

| File | Action |
|---|---|
| `py/tests/test_solver.py` | Update all references, add new tests |
| `py/examples/solver_basics.py` | Rename parameters |
| `py/examples/solver_line_fitting_p2.py` | Rename parameters, update `MVProductMatrix` usage |
| `py/examples/solver_point_line_p3.py` | Rename parameters, update `MVProductMatrix` usage |
| `py/examples/solver_rotor_estimation.py` | Rename parameters |