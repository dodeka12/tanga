# Phase 1 — BladeMask, MVMatrix, and parse utilities

← [Back to Overview](./overview.md)

> **Always consider the developer docs** under `docs/dev/` when implementing any step in this plan.  
> In particular: the [Python Coding Style Guide](../../../docs/dev/guides/py-coding-style-guide.md).  
> Also review any relevant architecture docs, use-case examples, and best practice documentation found there.

## Goal

Create three new pure-Python modules that form the foundation of `MVSolver`
and the `Algebra.random_mv()` method.  Keeping each concern in its own file
eliminates circular import risks:

```
_parse.py       — _parse_mv_string (moved from algebra.py)
blade_mask.py  — BladeMask
mv_matrix.py   — MVMatrix
```

Dependency order (no cycles):

```
_blade_names.py  (existing)
    └── _parse.py
         └── blade_mask.py   ←── algebra.py (TYPE_CHECKING only)
              └── mv_matrix.py
```

No C++ interaction is required in this phase.

---

## Steps

### 1.0 — Extract `_parse_mv_string` into `py/pytanga/_parse.py` ✓

Create `py/pytanga/_parse.py` and move `_TERM_RE` and `_parse_mv_string` from
`algebra.py` into it.  Update `algebra.py` to import them from `_parse`:

```python
from ._parse import _parse_mv_string
```

This makes the parser available to `blade_mask.py` (via `from ._parse import
_parse_mv_string`) without creating a dependency on `algebra.py`.

**Tests:** Verify that `Algebra.multivector("2 e1 - e2")` still works correctly
after the move.

### 1.1 — Create `py/pytanga/blade_mask.py` with `BladeMask` ✓

Create `py/pytanga/blade_mask.py`. Define `BladeMask` as a regular class.

`algebra.py` will import `BladeMask` (lazily, inside methods), so `blade_mask.py`
must **not** import `algebra.py` at module level.  Use `TYPE_CHECKING` for the
annotation only:

```python
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .algebra import Algebra
    from .mv import MV
```

**Internal structure** (two complementary views of the same data):

```python
class BladeMask:
    _ids:   tuple[int, ...]   # sorted, deduplicated blade ids — canonical order
    _index: dict[int, int]    # id → position, for O(1) index lookup
    _alg:   Algebra           # the algebra this mask belongs to
```

`__init__` signature:

```python
def __init__(
    self,
    alg,
    ids: Iterable[int] | str | Iterable[str] = (),
    *,
    grades: list[int] | None = None,
) -> None
```

Id resolution — performed in this order, results are unioned:

1. **`ids` is a `str`** — parse with `_parse_mv_string(ids, alg.dim)` and
   collect the resulting blade ids (signs and coefficients discarded).
   Example: `BladeMask(alg, "1 + e12 + e23")` → ids `{0, 3, 6}`.

2. **`ids` is an `Iterable[str]`** (i.e. non-empty and first element is `str`)
   — parse each element independently and union the resulting blade ids.
   Example: `BladeMask(alg, ["e12", "1 + e13"])` → ids `{0, 3, 5}`.

3. **`ids` is an `Iterable[int]`** (default) — collect directly.
   Example: `BladeMask(alg, [1, 2, 4])` — existing behaviour.

4. **`grades` keyword** — union in every blade id whose popcount equals any
   value in `grades`.  `grades=[0, 2]` adds the scalar and all grade-2 blades.
   Applied *after* `ids` so the two can be freely combined.
   Example: `BladeMask(alg, grades=[0, 2])` → the even-grade sub-algebra of
   grade ≤ 2 (scalar + bivectors in G(3,0): ids `{0, 3, 5, 6}`).

After resolution, sort and deduplicate:
```python
self._ids   = tuple(sorted(raw_ids))
self._index = {bid: i for i, bid in enumerate(self._ids)}
self._alg   = alg
```

**Classmethods:**

```python
@classmethod
def from_mv(cls, alg, a, only_nonzero: bool = True) -> "BladeMask"
```
Delegates to `alg._mod.blade_mask(a._impl, only_nonzero)` (added in Phase 2)
to get the raw id list, then calls `cls(alg, ids)`.

```python
@classmethod
def from_str(cls, alg, s: str) -> "BladeMask"
```
Convenience alias for `cls(alg, s)`.  Kept for explicitness; equivalent to
passing a string directly to `__init__`.

```python
@classmethod
def full(cls, alg) -> "BladeMask"
```
Returns `cls(alg, grades=list(range(alg.dim + 1)))` — all $2^{\text{dim}}$
blades (equivalent to `cls(alg, range(alg.algebra_dim))`).

**Properties and methods:**

```python
@property
def algebra(self)                       # the owning algebra

@property
def ids(self) -> list[int]             # copy of the sorted id list

def index(self, blade_id: int) -> int   # O(1) via _index; raises KeyError

def names(self) -> list[str]            # blade_name(id, alg.dim) for each id

def union(self, other: "BladeMask") -> "BladeMask"
def intersection(self, other: "BladeMask") -> "BladeMask"
# Both assert other._alg is self._alg.

def __len__ / __iter__ / __contains__ / __eq__ / __repr__
```

**Tests:** Construct `BladeMask(alg, [4, 1, 1, 2])` and verify `ids == [1, 2, 4]`
(sorted, deduplicated). Verify `index(2) == 1`. Verify `4 in mask` is `True`.
Verify `union` and `intersection` produce correct id sets.

String and grades construction:
- `BladeMask(alg, "1 + 2 e3 - e13").ids == [0, 4, 5]` for dim ≥ 3.
- `BladeMask(alg, ["e12", "1 + e13"]).ids == [0, 3, 5]`.
- `BladeMask(alg, grades=[0]).ids == [0]` (scalar only).
- `BladeMask(alg, grades=[2]).ids == [3, 5, 6]` in G(3,0) (all bivectors).
- `BladeMask(alg, grades=[0, 2]).ids == [0, 3, 5, 6]` (even sub-algebra).
- `BladeMask(alg, ["e1"], grades=[2]).ids == [1, 3, 5, 6]` (union of both).
- `BladeMask.full(alg).ids == list(range(8))` in G(3,0).
- `union` on masks from different algebras raises `AssertionError`.

### 1.2 — Create `py/pytanga/mv_matrix.py` with `MVMatrix` ✓

Create `py/pytanga/mv_matrix.py`.  Define `MVMatrix` as a `dataclass`:

```python
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from ._blade_mask import BladeMask

@dataclass
class MVMatrix:
    data:      np.ndarray        # shape (n_rows, n_cols); always a plain ndarray
    row_mask:  BladeMask         # blade mask labelling each row
    col_mask:  BladeMask | None = None   # blade mask labelling each column;
                                         # None (default) → empty mask (column vector)
```

Rules enforced in `__post_init__`:
- `data.ndim == 2`; raise `ValueError` otherwise.
- `len(row_mask) == data.shape[0]`; raise `ValueError` otherwise.
- If `col_mask` is `None`, set it to `BladeMask(row_mask._alg, [])`.  Use
  `object.__setattr__(self, 'col_mask', ...)` if the dataclass is frozen.
- When `col_mask` is non-empty, `len(col_mask) == data.shape[1]`;
  raise `ValueError` otherwise.
- `row_mask._alg is col_mask._alg`; raise `ValueError` otherwise.

Add convenience properties:
- `shape` → `data.shape`
- `is_column_vector` → `data.shape[1] == 1`
- `algebra` → `row_mask._alg`

**Tests:** Construct `MVMatrix` with valid inputs and verify `.shape`,
`.is_column_vector`, and `.algebra`. Verify mismatched `len(row_mask)` raises
`ValueError`. Verify mismatched algebras raises `ValueError`.
