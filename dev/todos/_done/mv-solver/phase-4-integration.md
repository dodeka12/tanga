# Phase 4 — Integration

← [Back to Overview](./overview.md)

> **Always consider the developer docs** under `docs/dev/` when implementing any step in this plan.  
> In particular: the [Python Coding Style Guide](../../../docs/dev/guides/py-coding-style-guide.md).  
> Also review any relevant architecture docs, use-case examples, and best practice documentation found there.

## Goal

Wire `MVSolver` into the rest of pytanga: add `Algebra.random_mv()` and the
`Algebra.solver` factory property, export all new public symbols from
`__init__.py`, and declare numpy as a dependency.

By the end of this phase the full public API is reachable from a single
`import pytanga` and the package metadata is correct.

---

## Steps

### 4.1 — Add `Algebra.random_mv()` ✓

Add to `py/pytanga/algebra.py`:

```python
def random_mv(
    self,
    *,
    low: float | int = -1,
    high: float | int = 1,
    mask: "BladeMask | None" = None,
    rng=None,
) -> "MV":
```

Behaviour:
- `low` and `high` define a half-open uniform range `[low, high)`, following
  numpy convention for both float and integer types.
- If `mask` is `None`, all blades of the algebra are populated; otherwise only
  the blades in `mask.ids` receive non-zero values.
- `rng` accepts a `numpy.random.Generator` (preferred), an integer seed, or
  `None` (creates a fresh generator).  Always call
  `numpy.random.default_rng(rng)` internally.
- For float dtypes (`float32`, `float64`): coefficients drawn from
  `rng.uniform(low, high, n)` cast to the algebra's dtype.
- For integer dtypes (`int32`, `int64`): coefficients drawn from
  `rng.integers(low, high, n)` (both endpoints integer, `high` exclusive).
  Zero values are allowed (unlike the C++ `GenRanMV` with non-zero guard).

Use a lazy import to avoid a circular dependency at module level:
```python
def random_mv(self, *, low=-1, high=1, mask=None, rng=None):
    import numpy as np
    from ._blade_mask import BladeMask
    ...
```

Type-hint `mask` under `TYPE_CHECKING` at the top of `algebra.py`:
```python
if TYPE_CHECKING:
    from ._blade_mask import BladeMask
```

**Tests:** In G(3,0) float64, verify `random_mv()` returns an MV with 8 blades
all populated. Verify `random_mv(mask=BladeMask(alg, [1,2,4]))` returns an MV
with only blades 1, 2, 4 non-zero.  Verify `random_mv(low=5, high=6)` returns
all coefficients in `[5.0, 6.0)`.  Verify integer algebra returns integer
coefficients.  Verify reproducibility: same seed gives same result.

### 4.2 — Add `Algebra.solver` property ✓

In `py/pytanga/algebra.py`, add a lazy-import property to `Algebra`:

```python
@property
def solver(self) -> "MVSolver":
    """Return an MVSolver bound to this algebra."""
    from .solver import MVSolver
    return MVSolver(self)
```

The lazy import avoids a circular dependency and keeps `algebra.py` free of a
hard numpy import at module level.

**Tests:** Verify `alg.solver` returns an `MVSolver` instance and that
`alg.solver._alg is alg`.

### 4.3 — Update `__init__.py` exports ✓

Add all new public symbols to `py/pytanga/__init__.py`:

```python
from ._blade_mask import BladeMask
from ._mv_matrix import MVMatrix
from .solver import MVSolver
```

Verify:
```python
from pytanga import Algebra, BladeMask, MVMatrix, MVSolver
```

**Tests:** Import all four directly from `pytanga` and verify they are the
same objects as those in their respective submodules.

### 4.4 — Declare numpy dependency ✓

Add `numpy` to the project's declared dependencies in `pyproject.toml` under
`[project] dependencies`.  numpy is already present in most scientific Python
environments but must be declared explicitly for correct packaging.

**Tests:** No code test required. Verify `uv pip show numpy` succeeds in the
project's virtual environment. Confirm `pyproject.toml` lists numpy.
