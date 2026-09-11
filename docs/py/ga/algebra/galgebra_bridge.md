# Galgebra Bridge

The `GalgebraBridge` class provides bidirectional conversion between
[galgebra](https://github.com/pygae/galgebra) (sympy‑based, symbolic) and
tanga (numeric) multivectors.  This enables symbolic derivation in galgebra
followed by numerical computation and visualization in tanga — or the reverse.

`GalgebraBridge` handles both **orthogonal** and **non‑orthogonal** galgebra
bases.  For non‑orthogonal bases it automatically diagonalizes the metric,
builds a grade‑wise transformation matrix, and inverts it for accurate
round‑trip conversion.

## Setup

galgebra is an optional dependency.  Install it with:

```bash
pip install "tanga-py[galgebra]"
```

Or in a uv‑managed project:

```bash
uv add "tanga-py[galgebra]"
```

## Quick Start

```python
import numpy as np
from galgebra.ga import Ga
from pytanga.algebra import GalgebraBridge

# 1. Create a galgebra algebra
ga = Ga('e1 e2 e3', g=[1, 1, 1])

# 2. Build the bridge — creates a matching tanga Algebra internally
bridge = GalgebraBridge(np.diag([1.0, 1.0, 1.0]), ga=ga)

# 3. Convert galgebra Mv → tanga MV
mv_ga = ga.mv([1.5, 2.0, 3.0], 'vector')
mv_tanga = bridge.from_galgebra(mv_ga)
bridge.show(mv_tanga, label='v')   # prints "v: 1.5 e1 + 2 e2 + 3 e3"

# 4. Compute with tanga, then convert back
result_ga = bridge.to_galgebra(mv_tanga * mv_tanga)
print(result_ga)                   # galgebra Mv with numeric coefficients
```

## Class Reference

### Constructor

```python
GalgebraBridge(
    metric,       # ndarray (n,n) or sympy Matrix — the galgebra metric
    *,
    ga=None,      # galgebra.ga.Ga, optional — enables to_galgebra() without arg
    dtype="float64",
    precision=1e-10,
)
```

The metric is eigendecomposed to determine:
- **Signature** — bitmask for the tanga `Algebra`
- **Basis vectors** — each galgebra basis vector expressed as a tanga MV
  (trivial for orthogonal bases, linear combinations for non‑orthogonal)
- **Display basis** — a complete named blade basis that shows galgebra blade
  names when printing tanga MVs
- **Transformation matrix** — 2ⁿ×2ⁿ forward matrix and its inverse for
  accurate coefficient mapping

### Properties

| Property | Type | Description |
|---|---|---|
| `bridge.algebra` | `Algebra` | The tanga Algebra instance (with galgebra display basis) |
| `bridge.dim` | `int` | Vector‑space dimension |
| `bridge.is_orthogonal` | `bool` | `True` if the metric was diagonal |

### Conversion Methods

| Method | Description |
|---|---|
| `bridge.from_galgebra(mv)` → `MV` | Convert galgebra `Mv` → tanga `MV`. Requires numeric coefficients (no symbols). |
| `bridge.to_galgebra(mv, ga=None)` → `Mv` | Convert tanga `MV` → galgebra `Mv`. Requires *ga* passed at init or as argument. |

### Display Methods

| Method | Description |
|---|---|
| `bridge.show(mv, label=\"\", fmt=None)` | Print *mv* in the galgebra display basis |
| `bridge.show_str(mv, label=\"\", fmt=None)` → `str` | Return string repr in the galgebra display basis |

These delegate to the tanga `Algebra`'s display, which was configured at bridge
construction to use galgebra's blade names (and linear combinations for
non‑orthogonal bases).

## Non‑Orthogonal Example

```python
import numpy as np
from galgebra.ga import Ga
from pytanga.algebra import GalgebraBridge

# Non‑diagonal 2D metric
g = np.array([[2.0, 1.0], [1.0, 2.0]])
ga = Ga('e1 e2', g=g.tolist())
bridge = GalgebraBridge(g, ga=ga)

print(bridge.is_orthogonal)  # → False

# galgebra basis vectors map to linear combinations in tanga:
e1 = ga.mv([1.0, 0.0], 'vector')
e1_t = bridge.from_galgebra(e1)
bridge.show(e1_t, label='e1')
# prints "e1: 1.414 e1" (or similar — the eigendecomposition handles it)

# Products still match:
e2 = ga.mv([0.0, 1.0], 'vector')
gp_ga = e1 * e2                    # galgebra GP
gp_t = bridge.from_galgebra(e1) * bridge.from_galgebra(e2)   # tanga GP
assert (bridge.to_galgebra(gp_t) - gp_ga).obj.expand() == 0  # ✓
```

## Round‑Trip Accuracy

The bridge uses `numpy.linalg.inv` on the full 2ⁿ×2ⁿ transformation matrix,
so round‑trip conversion is exact up to floating‑point precision (~1e‑15).
This has been verified for dimensions up to 5 (32×32 matrix) and works for
any dimension ≤ 8 (256×256 matrix).

```python
# Round‑trip preserves all coefficients
mv_ga = ga.mv([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])  # full E3 MV
mv_t = bridge.from_galgebra(mv_ga)
mv_back = bridge.to_galgebra(mv_t)
assert ((mv_back - mv_ga).obj.expand() == 0)   # ✓
```
