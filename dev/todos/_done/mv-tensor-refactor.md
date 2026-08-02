he # MVTensor Refactor — General Rank-Agnostic Tensor with Mask Labelling

## Goal

Replace the limited `MVProductTensor` class (hard-coded 3‑D with named fields `a_mask`/`b_mask`/`c_mask`) with a **general `MVTensor` class** that can hold multi-dimensional data of any rank, where each axis is labelled either by a `BladeMask` instance or by `None` (for non‑blade axes such as "list‑of‑multivectors" dimensions).

The `MVProductTensor` class is **removed** and replaced by a factory function that returns an `MVTensor`.  The `product_tensor()` solver function is updated to return an `MVTensor` instead of an `MVProductTensor`.

A new module-level `contract()` function provides an interface similar to `np.einsum()` but operates on `MVTensor` instances, automatically inferring the blade masks of the result from the contraction indices.

---

## Conceptual Model

An `MVTensor` has:
- `data : np.ndarray` — the raw N‑D array.
- `masks : tuple[BladeMask | None, ...]` — one per axis.  A `BladeMask` entry asserts that the axis is indexed by blade ids; a `None` entry means it is a "batch" or "counting" axis (e.g. a list of multivectors).

| Tensor type | Rank | masks | Example shape |
|-------------|------|-------|---------------|
| Single MV | 1 | `(BladeMask,)` | `(8,)` |
| List of MVs | 2 | `(BladeMask, None)` | `(8, 3)` |
| Product tensor (GP) | 3 | `(c_mask, a_mask, b_mask)` | `(8, 8, 8)` |
| Stacked product tensor (from MV list) | 4 | `(None, c_mask, a_mask, b_mask)` | `(n_mvs, 8, 8, 8)` |
| Stacked coefficients of MVs | 2 | `(None, BladeMask)` | `(3, 8)` |

---

## Files to Create / Modify

| File | Action | Purpose |
|------|--------|---------|
| `py/pytanga/mv_tensor.py` | **New** | `MVTensor` dataclass |
| `py/pytanga/mv_product_tensor.py` | **Delete** | Replaced by `MVTensor` |
| `py/pytanga/__init__.py` | Modify | Export `MVTensor`, remove `MVProductTensor` |
| `py/pytanga/solver/tensor_product.py` | Modify | Return `MVTensor` instead of `MVProductTensor` |
| `py/pytanga/solver/matrix_product.py` | Modify | Return `MVTensor` instead of `MVProductMatrix` (optional — can be a follow‑up) |
| `py/pytanga/solver/matrix_convert.py` | Modify | Add `to_tensor()` function |
| `py/pytanga/solver/tensor_contract.py` | **New** | `contract()` function |
| `py/tests/test_product_tensor.py` | Modify | Update to test `MVTensor` |
| `py/tests/test_mv_tensor.py` | **New** | Tests for `to_tensor` and `contract` |
| `py/examples/tensor_basics_01.py` | Modify | Adapt to new API |
| `py/examples/tensor_basics_02.py` | Modify | Adapt to new API |
| `dev/todos/mv-product-tensor-plan.md` | Update | Note that the plan has been superseded |

---

## Phase 1: `MVTensor` dataclass (`py/pytanga/mv_tensor.py`)

### Step 1.1 – Define the class

```python
@dataclass
class MVTensor:
    """A general N‑D tensor labelled by blade masks.

    Each axis is either associated with a ``BladeMask`` (the data along
    that axis is indexed by blade ids) or with ``None`` (the axis is a
    batch / counting dimension, e.g. a list of multivectors).

    Parameters
    ----------
    data : np.ndarray
        N‑D numpy array.
    masks : tuple[BladeMask | None, ...]
        One mask (or None) per axis.  ``len(masks) == data.ndim``.
    """

    data: np.ndarray
    masks: tuple[BladeMask | None, ...]

    def __post_init__(self) -> None:
        if len(self.masks) != self.data.ndim:
            raise ValueError(
                f"len(masks)={len(self.masks)} must equal data.ndim={self.data.ndim}"
            )
        for i, mask in enumerate(self.masks):
            if mask is not None and len(mask) != self.data.shape[i]:
                raise ValueError(
                    f"axis {i}: mask size {len(mask)} != data shape {self.data.shape[i]}"
                )

    @property
    def shape(self) -> tuple[int, ...]:
        return self.data.shape

    @property
    def algebra(self) -> "Algebra":
        for mask in self.masks:
            if mask is not None:
                return mask.algebra
        raise ValueError("MVTensor has no blade mask — cannot infer algebra")
```

Key design points:
- `masks` is a tuple, not a dict by axis name — this avoids the limitation of having to name every axis.
- Axes without blade masks are `None`.
- Validation ensures mask sizes match data shape per axis.
- `algebra` property finds the first non‑None mask to retrieve the algebra.

---

## Phase 2: `to_tensor()` function (`py/pytanga/solver/matrix_convert.py`)

### Step 2.1 – Add `to_tensor()`

```python
def to_tensor(
    a: MVLike | list[MVLike],
    *,
    mask: BladeMask | None = None,
    algebra: "Algebra | None" = None,
) -> MVTensor:
    """Convert one or more multivectors into an MVTensor.

    - Single MV → rank‑1 tensor with ``masks = (BladeMask,)``.
    - List of *n* MVs → rank‑2 tensor with ``masks = (BladeMask, None)``
      where axis 1 is the list‑ordering axis (no blade mask).

    Parameters
    ----------
    a : MVLike | list[MVLike]
        Single multivector or list thereof.
    mask : BladeMask | None
        Row index space.  If None, auto‑derived from the MV(s).
    algebra : Algebra | None
        Needed only when *a* is a bare string/scalar without mask context.
    """
    alg = ...  # resolve algebra as in to_matrix
    if mask is None:
        mask = BladeMask.full(alg) if isinstance(a, list) else BladeMask(...)

    if isinstance(a, list):
        mvs = [_as_mv(alg, x) for x in a]
        n = len(mvs)
        arr = np.zeros((len(mask), n), dtype=...)
        for i, mv in enumerate(mvs):
            mat = to_matrix(mv, mask=mask)
            arr[:, i] = mat.data[:, 0]
        return MVTensor(data=arr, masks=(mask, None))
    else:
        mv = _as_mv(alg, a)
        arr = to_matrix(mv, mask=mask).data.ravel()
        return MVTensor(data=arr, masks=(mask,))
```

---

## Phase 3: `contract()` function (`py/pytanga/solver/tensor_contract.py`)

### Step 3.1 – Core logic

The `contract()` function has the signature:

```python
def contract(subscripts: str, *tensors: MVTensor, **kwargs) -> MVTensor:
```

It performs the following steps:

1. **Parse the subscript** using `np.einsum_path` to determine:
   - Input axis labels
   - Output axis labels
   - Which axes are contracted

2. **Build the output masks**:
   - For each output axis label, find the axis it originated from in the input tensors.
   - If that input axis had a `BladeMask`, the output axis inherits it.
   - If it had `None`, the output axis also gets `None`.
   - If the same label appears on multiple input axes (a contraction), those axes **must** have the same mask (or at least compatible masks — same algebra and same ids).  Error if they differ.

3. **Call `np.einsum`** on the raw `.data` arrays.

4. **Wrap the result** in a new `MVTensor`.

### Step 3.2 – Example: GP contraction

```python
# O is rank-3 product tensor: masks = (c_mask, a_mask, b_mask)
# A is rank-1 MV tensor:       masks = (BladeMask,)
# B is rank-1 MV tensor:       masks = (BladeMask,)
C = contract("kij,i,j->k", O, A, B)
# C has masks = (O.masks[0],)  — inherits c_mask from O axis 0 (label 'k')
# Validates that A.masks[0] matches O.masks[1] (label 'i')
# Validates that B.masks[0] matches O.masks[2] (label 'j')
```

### Step 3.3 – Example: Batch GP contraction

```python
# O is rank-3 product tensor: masks = (c_mask, a_mask, b_mask)
# A is rank-2 MV tensor:      masks = (BladeMask, None)  — n MVs
# B is rank-2 MV tensor:      masks = (BladeMask, None)  — n MVs
C = contract("kij,in,jn->kn", O, A, B)
# C has masks = (c_mask, None)
# For each n, compute O @ A[:,n] @ B[:,n] and stack
```

### Step 3.4 – Mask compatibility check

When a label appears on multiple input axes, the corresponding masks must match:

```python
def _check_compatible(mask_a: BladeMask | None, mask_b: BladeMask | None) -> bool:
    if mask_a is None and mask_b is None:
        return True
    if mask_a is None or mask_b is None:
        return False  # can't mix None and BladeMask on same label
    return (mask_a.algebra is mask_b.algebra) and (mask_a.ids == mask_b.ids)
```

---

## Phase 4: Update `product_tensor()` function

### Step 4.1 – Change return type

`product_tensor()` in `py/pytanga/solver/tensor_product.py` currently returns `MVProductMatrix` (the 3‑D per‑MV product matrix class).  This should be changed to return `MVTensor`.

The new signature is identical except for the return type:

```python
def product_tensor(
    a_mask: BladeMask,
    b_mask: BladeMask,
    c_mask: BladeMask | None = None,
    *,
    product: EProduct = EProduct.GP,
    left: bool = True,
) -> MVTensor:
```

The function body builds a 3‑D numpy array via the C++ binding (same as today) and wraps it:

```python
return MVTensor(
    data=arr,
    masks=(c_mask, a_mask, b_mask),
)
```

### Step 4.2 – Remove `product` and `left` from the MVTensor

The `product` and `left` fields that were on `MVProductTensor` are **not** stored on the `MVTensor`.  They were metadata about how the tensor was built, not about its data.  If needed, the *caller* can track them.

---

## Phase 5: Cleanup — remove `MVProductTensor`

### Step 5.1 – Delete the file

Remove `py/pytanga/mv_product_tensor.py`.

### Step 5.2 – Update all imports

- `py/pytanga/__init__.py` — remove `MVProductTensor` export, add `MVTensor`
- `py/pytanga/solver/tensor_product.py` — import `MVTensor` instead
- `py/pytanga/solver/matrix_product.py` — import `MVTensor` (for `product_matrix_rev/conj` return values)
- `py/tests/test_product_tensor.py` — update assertions (remove `product`/`left` field checks)
- `py/examples/tensor_basics_01.py` — update
- `py/examples/tensor_basics_02.py` — update

### Step 5.3 – Update `MVProductMatrix` usage (optional, can be follow‑up)

`product_matrix()` currently returns `MVProductMatrix`.  This can be changed to return `MVTensor` as well, with masks `(None, c_mask, b_mask)` for single‑MV and `(None, c_mask, b_mask)` with extra axis for list.  This is **optional for this phase** — `MVProductMatrix` can coexist.

---

## Phase 6: Tests

### Step 6.1 – Update `test_product_tensor.py`

- Change all assertions: `T.product` → removed, `T.left` → removed
- Change `T.a_mask` → `T.masks[1]`, `T.b_mask` → `T.masks[2]`, `T.c_mask` → `T.masks[0]`
- Old `.contract(A_coeffs, B_coeffs)` calls → `contract("kij,i,j->k", T, A, B)`

### Step 6.2 – New `test_mv_tensor.py`

Tests for:
1. **`to_tensor()` single MV**: rank 1, masks `(BladeMask,)`, correct coefficients
2. **`to_tensor()` list of MVs**: rank 2, masks `(BladeMask, None)`, correct stacking
3. **`contract()` GP**: matches direct `A * B`
4. **`contract()` IP/OP**: matches direct products
5. **`contract()` batch GP**: `"kij,in,jn->kn"` for list inputs
6. **Mask incompatibility error**: contracting two tensors with mismatched masks on the same label
7. **Dimension mismatch error**: tensor shape doesn't match mask size

---

## Backward Compatibility

`MVProductTensor` is deleted.  Any external code that imports it will break and must be updated.  Since the `feat/product-tensors` branch has not been merged to `main`, this is acceptable.

`MVProductMatrix` is **preserved** for now to avoid scope creep.  A follow‑up phase can migrate it to `MVTensor` as well.

---

## Dependency Ordering

```
Phase 1 (MVTensor class)
    │
    ▼
Phase 2 (to_tensor() in matrix_convert.py)
    │
    ▼
Phase 3 (contract() in tensor_contract.py)
    │
    ▼
Phase 4 (Update product_tensor() to return MVTensor)
    │
    ▼
Phase 5 (Delete MVProductTensor, update all imports)
    │
    ▼
Phase 6 (Update/add tests)
```

---

## Estimated Effort

| Phase | Description | Effort |
|-------|-------------|--------|
| 1 | `MVTensor` dataclass | ~30 min |
| 2 | `to_tensor()` function | ~30 min |
| 3 | `contract()` function | ~1.5 h |
| 4 | Update `product_tensor()` | ~15 min |
| 5 | Delete `MVProductTensor`, update imports | ~30 min |
| 6 | Update/add tests | ~1 h |
| **Total** | | **~4.25 h** |

---

## Key Design Decisions

1. **Named axes vs positional masks**: The plan uses a tuple of `BladeMask | None` aligned with numpy axis positions, rather than dicts keyed by axis names.  This keeps the API simple and consistent with numpy.

2. **`contract()` vs `np.einsum()`**: The `contract()` function is a wrapper around `np.einsum` that additionally handles mask inference and validation.  The subscript syntax is identical.

3. **No product/left metadata on MVTensor**: The general tensor doesn't carry information about which GA product built it.  That belongs to the factory function (e.g. `product_tensor()`), not the data container.

4. **`MVProductMatrix` left for a follow‑up**: Converting `product_matrix()` to return `MVTensor` is straightforward but would touch many more files (all solver tests and examples).  This is deferred to keep the current phase focused.