# MVLabeledTensor — Label-Aware Tensor Operations Plan

## Goal

Introduce an `MVLabeledTensor` wrapper class that stores an `MVTensor` together with an axis-label string.  Overload `__getitem__` on both `MVTensor` and `MVLabeledTensor` so that `G["kij"]` returns a labeled tensor, while non‑string keys (integers, slices, tuples) are forwarded to the underlying `self.data` for standard NumPy indexing.  Overload arithmetic operators (`*`, `/`, `+`, `-`) on `MVLabeledTensor` to implement:
- Label-driven tensor contraction (like Einsum, inferred from shared labels).
- Element-wise multiplication flagged by a `_` suffix on index names.
- Division contraction via element-wise inverse then multiplication.
- Addition/subtraction of labeled tensors.
- Transpose via `__getitem__` arrow syntax (`B["ji->ij"]`).
- Standard NumPy slicing via `MVTensor.__getitem__` (e.g. `G[0:5]`, `G[:, 2]`).

---

## Terminology

| Term | Meaning |
|------|---------|
| **raw index name** | The user-visible label character, e.g. `"i"`, `"j"`, `"k"`, `"n"`. |
| **extended label** | The 2‑character axis descriptor: `"i*"` for contraction (default) or `"i_"` for element-wise.  The first character is the raw name; the second is `_` if element-wise, `*` if contractible.  This is the **user-facing format** as well as the internal format. |
| **label string** | The string stored on `MVLabeledTensor.labels`, consisting of one extended label per axis, e.g. `"k*i*j*"`. |

User-facing syntax matches the internal format exactly.  Each axis is written as `<char>[<mode>]` where `<mode>` is:
- `*` or **omitted** → contraction axis (default), e.g. `"i"`, `"i*"`, `"kij"`.
- `_` → element‑wise only, e.g. `"n_"`.

A label string like `"kij"` is canonicalised to `"k*i*j*"` (default `*` inserted for omitted modes).  `"in_"` is canonicalised to `"i*n_"` (contractible `i`, element‑wise `n`).  `"i*n_"` is accepted as‑is.  Underscores may **only** appear as the 2nd character of a label pair — leading or trailing `_` outside that position is an error.

---

## Files to Create / Modify

| File | Action | Purpose |
|------|--------|---------|
| `py/pytanga/tensor/_labeled.py` | **New** | `MVLabeledTensor` class |
| `py/pytanga/tensor/_data.py` | Modify | ✅ Phase 1 done: `MVTensor.__getitem__`, scalar arithmetic, and factory constructors |
| `py/pytanga/tensor/ops.py` | Modify | Add `_build_subscript()` helper |
| `py/pytanga/tensor/__init__.py` | Modify | Export `MVLabeledTensor` |
| `py/tests/test_labeled_tensor.py` | **New** | Comprehensive tests |
| `dev/todos/mv-labeled-tensor-plan.md` | **New** | This plan |

---

## Phase 1: Extend `MVTensor` with `__getitem__`, scalar ops, and factories

This phase adds only code to `_data.py` that does **not** depend on `MVLabeledTensor`.
`MVTensor.__getitem__` uses a lazy import of `MVLabeledTensor` (inside the method body)
so that the import works at runtime even though `MVLabeledTensor` is not yet created.
Everything else in this phase is self‑contained on `MVTensor`.

### 1.1 – `MVTensor.__getitem__`

```python
# In _data.py

def __getitem__(self, key) -> MVLabeledTensor | MVTensor | np.ndarray:
    if isinstance(key, str):
        from ._labeled import MVLabeledTensor
        return MVLabeledTensor(self, key)
    # Forward non‑string keys to the underlying numpy array
    result = self.data[key]
    if isinstance(result, np.ndarray):
        # Basic indexing: try to preserve mask metadata
        # … build new MVTensor with trimmed masks if ndim preserved
        # … fall back to raw ndarray for advanced/fancy indexing
        return _rebuild_mvtensor(self, key, result)
    return result
```

When `key` is a string, `MVTensor.__getitem__` creates an `MVLabeledTensor` (the transpose `"ji->ij"` case is handled inside `MVLabeledTensor.__getitem__`, not here).

When `key` is a slice, integer, tuple of slices/ints, or Ellipsis, the call is forwarded to `self.data[key]`.  A helper `_rebuild_mvtensor` attempts to infer the new masks:
- **Integer indexing** on an axis collapses it → remove that axis's mask.
- **Slice indexing** preserves the axis → keep that axis's mask.
- **Fancy indexing** (boolean arrays, integer arrays) → ambiguous mask semantics, fall back to raw `np.ndarray`.
- **Newaxis / None** → insert `None` mask at that position.

### 1.2 – Scalar member functions on `MVTensor`

```python
def mul_scalar(self, scalar: float) -> MVTensor:
    return MVTensor(data=self.data * scalar, masks=self.masks)

def div_scalar(self, scalar: float) -> MVTensor:
    return MVTensor(data=self.data / scalar, masks=self.masks)

def rdiv_scalar(self, scalar: float) -> MVTensor:
    """scalar / tensor, element‑wise."""
    return MVTensor(data=scalar / self.data, masks=self.masks)
```

### 1.3 – Factory constructors for zero‑initialised MVTensor

```python
# On MVTensor:

@staticmethod
def zeros(specs: list[BladeMask | int],
          dtype: np.dtype | str | None = None) -> MVTensor:
    """Create a zero-initialised MVTensor from a list of specifiers.

    Each element is either a ``BladeMask`` or an ``int``:

    - ``BladeMask`` → the axis uses that mask; its size is ``len(mask)``.
    - ``int`` → the axis has mask ``None`` (batch/counting axis); the
      integer gives the dimension size.

    The dtype defaults to ``float64`` unless a ``BladeMask`` is present,
    in which case it is inferred from the mask's algebra.
    """
    masks: list[BladeMask | None] = []
    shape: list[int] = []
    for spec in specs:
        if isinstance(spec, BladeMask):
            masks.append(spec)
            shape.append(len(spec))
        elif isinstance(spec, int):
            masks.append(None)
            shape.append(spec)
        else:
            raise TypeError(f"expected BladeMask or int, got {type(spec).__name__}")
    if dtype is None:
        dtype = np.float64
    return MVTensor(data=np.zeros(tuple(shape), dtype=dtype), masks=tuple(masks))

@staticmethod
def zeros_like(other: MVTensor, *, dtype: np.dtype | str | None = None) -> MVTensor:
    """Create a zero-initialised MVTensor with the same shape and masks as *other*."""
```

Example:

```python
mask = BladeMask(alg, [1, 2, 3])   # length 3
T = MVTensor.zeros([mask, 5, mask])
# T.masks = (mask, None, mask)
# T.shape = (3, 5, 3)
```

### 1.4 – `MVTensor.__setitem__`

MVTensor itself does **not** get a `__setitem__` overload.  Label‑aware assignment only makes sense on `MVLabeledTensor`.  Standard NumPy‑style assignment (`t[0:5] = x`) works through the existing data path since `MVTensor` is not frozen.

---

## Phase 2: `MVLabeledTensor` class (`_labeled.py`)

All label machinery lives here.  This phase produces a fully functional `MVLabeledTensor`
with `__getitem__`, `__setitem__`, label canonicalisation, `iter_labels`, and the
factory constructor `MVLabeledTensor.zeros`.

### 2.1 – Core structure

```python
@dataclass(frozen=True)
class MVLabeledTensor:
    tensor: MVTensor
    labels: str  # extended label string, length = 2 * tensor.ndim

    def __post_init__(self) -> None:
        _validate_labels(self.labels, self.tensor.data.ndim)
```

### 2.2 – Label validation & canonicalisation

Every label pair is `<char><mode>` where:
- `<char>` is a letter (raw index name, `a-zA-Z`)
- `<mode>` is `*` (contractible) or `_` (element-wise only)

When user passes `"kij"` (short form), it is canonicalised to `"k*i*j*"` (default `*` inserted).
When user passes `"in_"`, it is canonicalised to `"i*n_"`.
When user passes `"i*n_"`, it is accepted as‑is.

Helper:

```python
def _canonicalise(user_labels: str) -> str:
    """Convert user label string to extended label string.

    'kij'     → 'k*i*j*'
    'k*i*j*'  → 'k*i*j*'   (already canonical)
    'in_'     → 'i*n_'
    'i*n_'    → 'i*n_'     (already canonical)
    'i*n_j*'  → 'i*n_j*'   (already canonical)
    'ij_n'    → 'i*j*n_'   (short form mixed with explicit)
    '_i'      → error (underscore without preceding name)
    'i__'     → error (double underscore)
    'i_'      → 'i_'       (valid: single axis, element-wise)
    """
```

Rules:
- Parse the string into raw name + optional mode pairs.
- A raw name is a single letter (`a-zA-Z`).
- If the next character is `_`, the mode is element-wise.
- If the next character is `*` or another letter (or end of string), the mode is contraction (`*`).
- `_` must immediately follow a raw name; leading `_`, trailing `_` after a `_` mode, or `_` before any name are errors.
- After canonicalisation, `len(labels) == 2 * ndim`.

### 2.3 – `MVLabeledTensor.__getitem__`

Two modes:

1. **Relabel**: `A["ijk"]` → new `MVLabeledTensor` with updated labels (validated against ndim).
2. **Transpose/reorder**: `B["ij->ji"]`, `B["kij->jki"]` → parse arrow expression, permute axes.

```python
def __getitem__(self, key) -> MVLabeledTensor:
    if isinstance(key, str):
        if "->" in key:
            return _transpose(self, key)
        return MVLabeledTensor(self.tensor, _canonicalise(key))
    # Non‑string keys: forward to self.tensor.__getitem__
    return self.tensor[key]
```

`_transpose(src_labels: str)`:
- Parse `"kij->jki"` into source raw names `"kij"` and target raw names `"jki"`.
- Validate that `len(source) == ndim` and `set(source) == set(target)` (same set of names, just reordered).
- Build the permutation `axes`: for each target name at position `t`, find the source axis `s` where that name appears.
- Use `np.transpose(tensor.data, axes)` — this returns a **view** when possible (no data copy for pure permutations).
- Reorder `tensor.masks` by the same `axes` permutation.
- Return `MVLabeledTensor(new_tensor, _canonicalise(target_labels))`.

General examples:
- `B["ij->ji"]` → transpose axes 0↔1
- `B["kij->jki"]` → cyclic shift axes (0,1,2) → (1,2,0)
- `B["ijk->kji"]` → reverse all axes

The target labels are canonicalised (default `*` inserted) before creating the result.

Non‑string keys (slices, integers, tuples) on `MVLabeledTensor` are forwarded to `self.tensor[key]`, which delegates to `MVTensor.__getitem__`.

### 2.4 – Decompose labels into raw names for contraction building

```python
def _raw_names(extended_labels: str) -> str:
    """Extract raw names from extended labels: 'k*i*j*' → 'kij'."""

def _is_elemwise(extended_labels: str, axis: int) -> bool:
    """Check if axis at position *axis* is marked element‑wise."""
```

### 2.5 – `MVLabeledTensor.__setitem__` — assignment from another labeled tensor

```python
# On MVLabeledTensor:

def __setitem__(self, key, value: MVLabeledTensor) -> None:
    """Assign data from *value* into *self* according to label alignment.

    Usage:  A["kij"] = B["ji"]

    Algorithm:
    1. *key* is a user label string; canonicalise it.
    2. Validate that *key* matches ``self.labels`` (same set of raw names and
       element‑wise modes — the string is just confirming/selecting the view).
    3. Compare ``self`` raw names with ``value`` raw names:
       - **Shared names**: the corresponding axes must have compatible masks
         and the same length.  These axes are aligned.
       - **Names in self but not value**: B is broadcast along these axes
         (i.e. the value data is repeated).
       - **Names in value but not self**: ValueError (cannot drop axes during
         assignment).
    4. Build a subscript ``"src_labels->dst_labels"`` where *src_labels* are the
       raw names of value and *dst_labels* are the raw names of self.
    5. Use ``np.einsum`` with this subscript to broadcast/transpose value.data
       into ``self.data``, then assign in‑place::
           self.data[:] = np.einsum(subscripts, value.data)
    """
```

Example:

```python
# A is an existing MVLabeledTensor with labels "k*i*j*" (rank 3)
# B is an MVLabeledTensor with labels "j*i*" (rank 2)
# Both use the same algebra/masks for "i" and "j"

A["kij"] = B["ji"]
# Internally:
#   self labels: k*i*j*  → raw: kij
#   value labels: j*i*  → raw: ji
#   shared: {i, j}, self‑only: {k}
#   subscript: "ji->kij"  (broadcast B along the 'k' axis)
#   np.einsum("ji->kij", B.tensor.data) → broadcast to A.shape, then assign
```

Key edge case: if *value* is a plain `MVTensor` (not labeled), it is treated as having `_canonicalise(key)` as its labels — i.e., the labels are inferred from the `__setitem__` key itself.  This allows `A["kij"] = T` where `T` is an unlabeled tensor of the same shape.

### 2.6 – Factory constructors on `MVLabeledTensor`

```python
@staticmethod
def zeros(labels: str,
          specs: list[BladeMask | int],
          dtype: np.dtype | str | None = None) -> MVLabeledTensor:
    """Create a zero-initialised MVLabeledTensor.

    Parameters
    ----------
    labels : str
        User label string (canonicalised internally).
    specs : list[BladeMask | int]
        Same semantics as ``MVTensor.zeros``.  Must match ``ndim``.
    """
    tensor = MVTensor.zeros(specs, dtype=dtype)
    return MVLabeledTensor(tensor, labels)
```

For convenience, a per‑label‑name variant:

```python
@staticmethod
def zeros_from_dict(labels: str,
                    specs: dict[str, BladeMask | int],
                    dtype: np.dtype | str | None = None) -> MVLabeledTensor:
    """Create a zero-initialised MVLabeledTensor from per‑label specs.

    Parameters
    ----------
    labels : str
        User label string, e.g. ``"kij"`` (each raw name must appear as a key).
    specs : dict[str, BladeMask | int]
        Maps raw index names to a ``BladeMask`` or an integer size.
        Each raw name in *labels* must appear exactly once in *specs*.
    """
    raw = _raw_names(_canonicalise(labels))
    positional_specs = [specs[name] for name in raw]
    return MVLabeledTensor.zeros(labels, positional_specs, dtype=dtype)
```

### 2.7 – Label‑based iterator: `iter_labels()`

A module‑level generator that iterates synchronously over a named label across one or more `MVLabeledTensor` instances.

```python
# In _labeled.py

def iter_labels(name: str, *tensors: MVLabeledTensor):
    """Iterate synchronously over label *name* across all tensors.

    Yields a tuple of ``MVLabeledTensor`` (one per input tensor) where
    the named axis has been collapsed (removed) by slicing along it.
    If only one tensor is passed, yields single ``MVLabeledTensor``
    instances (not a 1‑tuple).

    Parameters
    ----------
    name : str
        Single raw index name to iterate over, e.g. ``"n"``.
    *tensors : MVLabeledTensor
        All tensors must contain *name* with compatible masks and the
        same axis length.

    Yields
    ------
    MVLabeledTensor | tuple[MVLabeledTensor, ...]
    """
    axes: list[int] = []
    for t in tensors:
        raw = _raw_names(t.labels)
        if name not in raw:
            raise ValueError(f"label '{name}' not found in tensor with labels {t.labels}")
        axes.append(raw.index(name))

    length = tensors[0].tensor.shape[axes[0]]
    if not all(t.tensor.shape[ax] == length for t, ax in zip(tensors, axes)):
        raise ValueError(f"label '{name}' has mismatched axis lengths across tensors")

    for i in range(length):
        slices = []
        for t, ax in zip(tensors, axes):
            sliced_data = t.tensor.data.take(i, axis=ax)
            # drop the iterated axis from masks
            sliced_masks = t.tensor.masks[:ax] + t.tensor.masks[ax+1:]
            # drop the iterated label from the label string (2 chars)
            sliced_labels = t.labels[:2*ax] + t.labels[2*ax+2:]
            slices.append(MVLabeledTensor(
                MVTensor(data=sliced_data, masks=sliced_masks), sliced_labels))
        yield tuple(slices) if len(slices) > 1 else slices[0]
```

**Usage example:**

```python
# A has labels "i*n*", shape (|mask|, 5)
# B has labels "j*n*", shape (|mask|, 5)

for A_slice, B_slice in iter_labels("n", A, B):
    # A_slice.labels == "i*"  (n removed), shape (|mask|,)
    # B_slice.labels == "j*"  (n removed), shape (|mask|,)
    C_slice = A_slice["i"] * B_slice["j"]  # outer product per iteration
    # … accumulate or assign …
```

**Single‑tensor iteration:**

```python
for Ai in iter_labels("n", A):
    # Ai is MVLabeledTensor with label "n" removed
```

**Key design points:**
- The iterated axis is **removed** (not kept as size‑1), matching `np.take(i, axis=ax)` semantics.
- Works identically for contraction (`*`) and element‑wise (`_`) axes — the mode doesn't affect iteration.
- Mask compatibility is already enforced by `MVLabeledTensor` construction; axis‑length consistency is checked explicitly.
- `iter_labels` is a standalone function, not a method — this keeps `MVLabeledTensor` clean and avoids the ambiguity of which tensor "owns" the iteration.

---

## Phase 3: `_build_subscript` helper in `ops.py`

Extract the subscript-building logic into a shared helper in `ops.py` so that
`contract()` and `MVLabeledTensor.__mul__` use the same code path.  This is
implemented **before** the operators so they can rely on it from the start.

```python
def _build_subscript(*labeled_tensors: MVLabeledTensor) -> tuple[str, list[str], dict[str, str]]:
    """Given labeled tensors, build an einsum subscript and output labels.

    Parameters
    ----------
    *labeled_tensors : MVLabeledTensor
        The labeled tensors participating in the operation.

    Returns
    -------
    subscripts : str
        The full einsum subscript, e.g. ``"kij,in,jn->kn"``.
    output_raw : list[str]
        Raw names of the output axes, in order.
    output_modes : dict[str, str]
        Maps each output raw name to its mode (``'*'`` or ``'_'``).
    """
```

This phase also adds a `contract_labeled` convenience wrapper that calls
`_build_subscript` and then delegates to the existing `contract()`.

---

## Phase 4: Contraction `__mul__`

### 3.1 – Core algorithm for `A["..."] * B["..."]`

1. Get extended label strings `la`, `lb`.
2. Decompose raw names: `raw_a`, `raw_b`.
3. Find intersection of raw names: `shared = set(raw_a) & set(raw_b)`.
4. For each shared name, check element-wise status:
   - If **both** are contractible (both `*`), it is a **contraction** axis.
   - If **either** is element-wise (`_`), it is an **element‑wise multiplication** axis (no summation), and it stays in the output.
5. Build the output label string:
   - All raw names from `raw_a` that are not contracted, in order.
   - All raw names from `raw_b` that are not contracted and not already present, in order.
   - For each output axis, determine extended status: inherit from whichever input provided it (both must agree on `*` vs `_` if the name came from both; if they differ, `_` wins).
6. Build the Einsum subscript: `"raz,raz->outz"` using raw names.
   - For element‑wise shared axes, they appear in both inputs AND the output (no summation).
   - For contracted shared axes, they appear in both inputs but NOT the output.
7. Call `contract(subscripts, t_a, t_b)`.
8. Wrap result in `MVLabeledTensor` with the computed output extended labels.

### 3.2 – Examples

| Expression | raw_a | raw_b | Contraction | Output raw | Einsum subscript |
|------------|-------|-------|-------------|------------|------------------|
| `G["kij"] * A["i"]` | `kij` | `i` | `i` | `kj` | `"kij,i->kj"` |
| `A["in_"] * B["jn_"]` | `in_` | `jn_` | none (`_` on both) | `ijn_` | `"in,jn->ijn"` (element-wise on `n`) |
| `A["in_"] * B["jn"]` | `in_` | `jn` | none (`_` on self) | `ijn_` | `"in,jn->ijn"` |
| `A["in"] * B["jn_"]` | `in` | `jn_` | none (`_` on other) | `ijn_` | `"in,jn->ijn"` |
| `A["ij"] * B["jk"]` | `ij` | `jk` | `j` | `ik` | `"ij,jk->ik"` |
| `A["ij"] * B["kl"]` | `ij` | `kl` | none | `ijkl` | `"ij,kl->ijkl"` |

### 3.3 – Mask compatibility for element‑wise axes

When a label appears as element‑wise on both inputs, the axis remains in the output.  The masks from both inputs must still be **compatible** (same blade ids, same algebra), because they will be aligned for element‑wise multiplication.  This is enforced by `contract()`'s existing validation.

### 3.4 – Scalar times `MVLabeledTensor`

```python
# On MVLabeledTensor:
def mul_scalar(self, scalar: float) -> MVLabeledTensor:
    return MVLabeledTensor(self.tensor.mul_scalar(scalar), self.labels)

def div_scalar(self, scalar: float) -> MVLabeledTensor:
    return MVLabeledTensor(self.tensor.div_scalar(scalar), self.labels)

def rdiv_scalar(self, scalar: float) -> MVLabeledTensor:
    return MVLabeledTensor(self.tensor.rdiv_scalar(scalar), self.labels)
```

`MVTensor.mul_scalar` etc. are defined in Phase 1.

---

## Phase 5: Division contraction `__truediv__` and `__rtruediv__`

### 4.1 – `A["ij"] / B["jk"]`

1. Compute `B_inv = 1 / B["jk"]` → element-wise reciprocal on the tensor data.
2. Compute `C = A["ij"] * B_inv["jk"]` using the `__mul__` logic.
3. Return `C`.

### 4.2 – `1 / B["jk"]`

1. Compute `data = 1.0 / B.tensor.data` (element-wise reciprocal).
2. Return `MVLabeledTensor(MVTensor(data=data, masks=B.tensor.masks), B.labels)`.

### 4.3 – Scalar division edge case

`A["ij"] / scalar` → `A.div_scalar(scalar)`.
`scalar / A["ij"]` → `A.rdiv_scalar(scalar)`.

---

## Phase 6: Addition and subtraction

### 5.1 – `A["ij"] + B["jk"]` → `C["ijk"]`

Goal: broadcast-add two tensors, aligning on shared label `"j"`.  The output has the union of all labels from both inputs, in order (self labels first, then other labels not already present).

Algorithm:
1. Get raw names `raw_a`, `raw_b`.
2. Find shared raw names.
3. For each shared name: the corresponding axes must have the same length and compatible masks.  They will be "broadcast" together (not summed — they are already aligned).
4. Build the output raw names: `raw_a` followed by raw names from `raw_b` that are not in `raw_a`.
5. Use `np.broadcast` or explicit `np.expand_dims` + `np.add` to align the two tensors on all output axes.
6. Result is an `MVLabeledTensor` whose labels are the canonicalised output labels.
   - Output extended labels: inherit from `A` for names originating from `A`, from `B` for names originating from `B`.
   - For shared names: masks must be compatible; extended label from `A` wins if both are `*`, otherwise `_` wins.

### 5.2 – `A["ij"] - B["jk"]` → same as addition with `np.subtract`.

### 5.3 – Edge case: `A["ij"] + B["ij"]` (same labels)

This is a direct element-wise addition; result keeps labels `"ij"`.

### 5.4 – Error: incompatible shared axes

If `A["ij"] + B["ij"]` but the `j` masks differ → `ValueError`.

---

## Phase 7: Integration & exports

### 6.1 – `py/pytanga/tensor/__init__.py`

```python
from ._data import MVTensor
from ._labeled import MVLabeledTensor

__all__ = ["MVTensor", "MVLabeledTensor"]
```

### 6.2 – No circular imports

`_labeled.py` imports from `_data.py` and `ops.py`.
`_data.py` imports from `_labeled.py` only inside `__getitem__` (lazy import).
`ops.py` is imported by `_labeled.py` for `contract()`.

---

## Phase 8: Tests (`test_labeled_tensor.py`)

### 7.1 – Label canonicalisation

- `"kij"` → `"k*i*j*"`
- `"k*i*j*"` → `"k*i*j*"` (no‑op)
- `"in_"` → `"i*n_"`
- `"i*n_"` → `"i*n_"` (no‑op)
- `"ij_n"` → `"i*j*n_"`
- `"i*n_j*"` → `"i*n_j*"` (no‑op)
- `"i_"` → `"i_"` (single axis, element-wise)
- `"_i"` → error (underscore before any name)
- `"i__"` → error (double underscore)
- `"_"` → error (bare underscore)

### 7.2 – `__getitem__` on MVTensor

- `to_tensor(mv, mask=full)["i"]` returns `MVLabeledTensor` with labels `"i*"`.
- `product_tensor(a,b)["kij"]` returns `MVLabeledTensor` with labels `"k*i*j*"`.

### 7.3 – `__getitem__` slicing on MVTensor

- `G[0:5]` on a rank‑1 tensor returns a new `MVTensor` with sliced data and same mask.
- `G[2]` on a rank‑1 tensor returns a new `MVTensor` with a scalar (0‑dim) data.
- `G[:, 0:5]` on a rank‑2 tensor returns a new `MVTensor` with sliced data and same masks.
- `G[0, :]` on a rank‑2 tensor returns a rank‑1 `MVTensor` (one mask dropped).
- `G[[0, 1, 3]]` (fancy indexing) → falls back to raw `np.ndarray`.

### 7.4 – `__getitem__` with transpose/reorder on MVLabeledTensor

- `t["ij->ji"]` on a rank-2 labeled tensor transposes axes (returns view when possible).
- `t["kij->jki"]` on a rank-3 labeled tensor cyclically permutes axes.
- `t["ijk->kji"]` reverses all axes.
- Verify that data is a view (`np.may_share_memory`) for pure permutations.
- Invalid permutation (`"ij->jk"` with different label sets) → error.

### 7.5 – Contraction `__mul__`

- Basic GP: `O["kij"] * A["i"] * B["j"]` matches `A * B`.
- Batch GP: `O["kij"] * A["in"] * B["jn"]` matches batch GP.
- Outer product: `A["i"] * B["j"]` → `"ij"`.

### 7.6 – Element-wise `_` suffix

- `A["in_"] * B["jn_"]` → `"in,jn->ijn"` element-wise on `n`.
- `A["in_"] * B["jn"]` → same result (only one needs `_`; the mode defaults to `*` on the other, but `_` wins for the shared axis).
- `A["i*n_"] * B["j*n_"]` → same, explicit format.
- Verify output data matches the expected element-wise multiplication.

### 7.7 – Division

- `A["ij"] / B["jk"]` → verify against explicit `1/B` then `*`.
- `1 / B["jk"]` → verify element-wise reciprocal.

### 7.8 – Addition / subtraction

- `A["ij"] + B["jk"]` → broadcast add, output `"ijk"`.
- `A["ij"] + B["ij"]` → direct element-wise add.
- `A["ij"] - B["ij"]` → direct element-wise subtract.
- Mask incompatibility on shared axis → error.

### 7.9 – Scalar ops

- `t.mul_scalar(2.0)` → data doubled, labels preserved.
- `t.div_scalar(2.0)` → data halved, labels preserved.
- `t.rdiv_scalar(2.0)` → `2.0 / data`, labels preserved.

### 7.10 – Chaining

- `O["kij"] * A["i"] * B["j"]` — the result of the first `*` is an `MVLabeledTensor`, which via `__mul__` contracts with `B["j"]`.
- Verify the final result.

### 7.11 – Factory constructors (`zeros`)

- `MVTensor.zeros([mask, 5, mask])` returns a rank‑3 zero tensor, masks = `(mask, None, mask)`, shape = `(len(mask), 5, len(mask))`.
- `MVTensor.zeros([3])` (bare int) → rank‑1, masks = `(None,)`, shape = `(3,)`.
- `MVTensor.zeros_like(existing)` returns same‑shape zero tensor matching *existing*.
- Invalid spec (float, None) → `TypeError`.
- `MVLabeledTensor.zeros("kij", [c_mask, a_mask, b_mask])` returns a labeled zero tensor with canonicalised labels.
- `MVLabeledTensor.zeros_from_dict("in", {"i": blade_mask, "n": 5})` creates shape `(len(blade_mask), 5)` with labels `"i*n*"`.
- Missing label in `zeros_from_dict` specs dict → error.

### 7.12 – `__setitem__` assignment

- `A["kij"] = B["ji"]` — assign rank‑2 data into rank‑3 target; broadcast along `"k"`.
- `A["ij"] = B["ij"]` — direct assignment when labels match exactly.
- `A["ij"] = B["ji"]` — assignment with implicit transpose.
- `A["kij"] = T` where `T` is a plain `MVTensor` — labels inferred from key.
- `A["ij"] = B["jk"]` → ValueError (value has extra label `"k"` not in target).
- Verify data correctness after assignment.

### 7.13 – `iter_labels`

- Single tensor: `for Ai in iter_labels("n", A):` yields `MVLabeledTensor` with `"n"` removed, one per slice.
- Multiple tensors: `for A_n, B_n in iter_labels("n", A, B):` yields tuples of slices in lockstep.
- Verify each slice has correct labels and data.
- Mismatched axis lengths on the iterated label → `ValueError`.
- Label not present in one tensor → `ValueError`.
- Works with both contraction (`*`) and element‑wise (`_`) axes.

---

## Design Decisions

1. **`frozen=True` on `MVLabeledTensor`**: A labeled tensor is a `(tensor, labels)` pair.  Modifying labels in-place would violate the contract.  New labels mean a new instance.

2. **Labels stored in canonical (extended) form**: The user may write `A["ij"]`, `A["i*j*"]`, or `A["ij_"]`.  All forms are canonicalised to the same internal format (`"i*j*"`, `"i*j_"`, etc.) and stored that way on the `MVLabeledTensor`.  The `repr()` shows the canonical form.

3. **`np.einsum` does the heavy lifting**: Subscript strings are built from label analysis, then delegated to the existing `contract()` function.  This ensures mask validation and propagation are handled consistently.

4. **Element‑wise via shared label in output**: When a shared label is element‑wise (`_`), it appears in both inputs AND the output in the Einsum subscript.  `np.einsum("in,jn->ijn", ...)` naturally performs element‑wise multiplication on the `n` axis.

5. **Addition uses broadcasting**: We use `np.add` with explicit broadcasting, not `np.einsum`.  This is the natural operation for `+`.

6. **`__getitem__` dispatch**: String keys are interpreted as label/transpose expressions; all other keys (slices, integers, tuples) are forwarded to `self.data[key]` for standard NumPy indexing.  Mask metadata is preserved when possible (basic slicing) and dropped for ambiguous cases (fancy indexing).

7. **Transpose via `__getitem__` arrow syntax**: `B["ji->ij"]` is parsed inside `MVLabeledTensor.__getitem__`.  The arrow separates source labels from target labels.  `np.transpose` is used for zero‑copy reordering.

---

## Dependency Ordering

```
Phase 1 (MVTensor.__getitem__, scalar ops, factories)
    │
    ▼
Phase 2 (MVLabeledTensor class, label canonicalisation, __getitem__,
        __setitem__, factories, iter_labels)
    │
    ▼
Phase 3 (_build_subscript helper in ops.py)
    │
    ▼
Phase 4 (__mul__ contraction logic)
    │
    ▼
Phase 5 (__truediv__ / __rtruediv__)
    │
    ▼
Phase 6 (__add__ / __sub__)
    │
    ▼
Phase 7 (Integration & exports)
    │
    ▼
Phase 8 (Tests)
```

---

## Estimated Effort

| Phase | Description | Effort |
|-------|-------------|--------|
| 1 | `MVTensor.__getitem__`, scalar ops, factories | ~30 min |
| 2 | `MVLabeledTensor` class, labels, `__getitem__`, `__setitem__`, factories, `iter_labels` | ~1.5 h |
| 3 | `_build_subscript` helper in ops.py | ~30 min |
| 4 | `__mul__` contraction | ~1.5 h |
| 5 | `__truediv__` / `__rtruediv__` | ~30 min |
| 6 | `__add__` / `__sub__` | ~1 h |
| 7 | Integration & exports | ~15 min |
| 8 | Tests | ~2.5 h |
| **Total** | | **~8 h** |

---

## Changes from Original Plan

| Change | Rationale |
|--------|-----------|
| Moved `MVLabeledTensor.__setitem__` (was 1.4) → Phase 2.5 | Depends on `_canonicalise()`, `_raw_names()`, and the `MVLabeledTensor` class itself — none of which exist until Phase 2. |
| Moved `iter_labels()` (was 1.6) → Phase 2.7 | Uses `MVLabeledTensor`, `_raw_names()`, and `MVTensor` constructor with label slicing — all Phase 2 concerns. |
| Moved `MVLabeledTensor.zeros` / `zeros_from_dict` (was 1.3) → Phase 2.6 | Requires `_canonicalise()`, `_raw_names()`, and `MVLabeledTensor` — all Phase 2. |
| `MVTensor.zeros` / `zeros_like` stays in Phase 1.3 | Self‑contained on `MVTensor`, no dependency on `MVLabeledTensor`. |
| Phase 1.5 (`MVTensor.__setitem__` note) → Phase 1.4 | Renumbered after removal of old 1.4. |