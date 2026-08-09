# Solvers

Every solver function (`solve`, `solve_lsq`, `solve_mod`) follows the same
internal pipeline:

1. **Determine blade masks** — which blades does A occupy?  From the output
   blades of Y, what is the maximal subspace X can live in?  See
   [Blade Mask Pipeline](blade-mask-pipeline.md).

2. **Build the product matrix** — a dense linear system mapping X's
   coefficients to Y's coefficients.  See
   [Matrix Primitives](matrix-primitives.md).

3. **Solve the linear system** — with the appropriate backend.

```python
from pytanga.solver.solve import solve, solve_lsq, solve_mod
```

## `solve` — float, full‑rank system

```python
from pytanga import Algebra
from pytanga.basis import BasisE3
from pytanga.solver.solve import solve

alg = BasisE3(dtype="float64")

X = solve(A, Y, algebra=alg)
X = solve(A, Y, product='op', left=False, algebra=alg)
```

Automatically derives `a_mask`, `b_mask`, and `c_mask` from the non‑zero
blades of A and Y.  Delegates to `numpy.linalg.solve`.

**When to use**: A is non‑singular and the system is exactly determined.

**When it fails**:
- `TypeError` — the algebra uses an integer dtype (use `solve_mod`).
- `numpy.linalg.LinAlgError` — A is singular (try `solve_lsq`).

### Example — float inverse

```python
from pytanga import Algebra
from pytanga.basis import BasisE3
from pytanga.solver.solve import solve

alg = BasisE3(dtype="float64")
A = alg.random_mv(rng=42)

X = solve(A, 1.0, algebra=alg)            # solve A * X = 1

check = A * X
check.prune()
print(check)                                # "1.0"
```

## `solve_lsq` — least‑squares

Uses `numpy.linalg.lstsq`.  Handles rank‑deficient and overdetermined
systems.  Pass lists of A and C to stack multiple equations:

```python
X = solve_lsq(A, C, algebra=alg)
X = solve_lsq(A, C, tol=1e-10, algebra=alg)
X = solve_lsq([A1, A2], [C1, C2], algebra=alg)
```

### Example — homogeneous line fitting in P2

```python
from pytanga import BladeMask
from pytanga.solver.solve import solve_lsq
from pytanga.matrix.product import product_matrix
from pytanga.matrix.convert import from_matrix
import numpy as np

col_mask = BladeMask(alg, grades=[2])          # lines are bivectors
row_mask = BladeMask(alg, grades=[3])          # output is pseudoscalar

# Stack points into a product matrix
M = product_matrix(points, a_mask=col_mask,
                   b_mask=col_mask, c_mask=row_mask, product='op')

_, _, Vt = np.linalg.svd(M.data.reshape(-1, len(col_mask)), full_matrices=True)
L_vec = Vt[-1]
L = from_matrix(L_vec.reshape(-1, 1), M.b_mask)
```

## `solve_mod` — modular integer systems

Runs Gaussian elimination in C++ (`CCongruence_HMod`).  The modulus should
be prime for full invertibility.

```python
from pytanga.solver.solve import solve_mod

alg_i = BasisE3(dtype="int64")
A = alg_i({"e1": 3, "e2": 5, 0: 1})

X = solve_mod(A, 1, modulus=97, algebra=alg_i)   # A * X ≡ 1 (mod 97)
```

Raises `RuntimeError` when no unique solution exists modulo the given
modulus.  Raises `TypeError` for float algebras.

## Specifying masks explicitly

All three solvers accept optional `a_mask`, `b_mask`, and `c_mask`:

```python
a_mask = BladeMask(alg, "e1 + e2")
c_mask = BladeMask.full(alg)
X = solve(A, 1.0, a_mask=a_mask, c_mask=c_mask, algebra=alg)
```

When `b_mask` is omitted, it is computed via `inverse_blade_mask(a_mask, c_mask)`.