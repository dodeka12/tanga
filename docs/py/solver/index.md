# Equation Solving

The `pytanga.solver` submodule converts geometric algebra product equations
(`A ∘ X = Y`) into linear systems and solves them.  The three solvers —
[`solve`](solve.md), [`solve_lsq`](solve.md), and [`solve_mod`](solve.md) —
are free functions that derive blade masks automatically from the input
multivectors, build a product matrix via the [matrix primitives](matrix-primitives.md),
and delegate to `numpy.linalg` for floating‑point systems or to C++ Gaussian
elimination for modular integer systems.  The [blade mask pipeline](blade-mask-pipeline.md)
explains how `product_blade_mask` and `inverse_blade_mask` determine the
subspace of the unknown.  [`EProduct`](enums.md) and [`EInv`](enums.md) enums
control which GA product is used and whether involutions are applied.

```python
from pytanga.solver.solve import solve, solve_lsq, solve_mod
```

## Reference

| Topic | Guide |
|-------|-------|
| `solve`, `solve_lsq`, `solve_mod` — high‑level solver interfaces | [Solvers](solve.md) |
| `product_blade_mask`, `inverse_blade_mask` — automatic subspace derivation | [Blade Mask Pipeline](blade-mask-pipeline.md) |
| `to_matrix`, `from_matrix`, `product_matrix` — matrix building functions | [Matrix Primitives](matrix-primitives.md) |
| `EProduct`, `EInv` enums and input coercion | [Enums & Coercion](enums.md) |

## Quick start

```python
from pytanga import Algebra
from pytanga.basis import BasisE3
from pytanga.solver.solve import solve

alg = BasisE3(dtype="float64")

# Solve A * X = 1 (multiplicative inverse)
A = alg.random_mv(rng=42)
X = solve(A, 1.0, algebra=alg)

# Verify
check = A * X
check.prune()
print(check)   # "1.0"
```
