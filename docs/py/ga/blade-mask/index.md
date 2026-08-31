# BladeMask

A `BladeMask` is an ordered, deduplicated set of blade IDs belonging to a
specific algebra.  It is the fundamental type that labels rows, columns, and
tensor axes throughout pytanga's matrix, solver, and tensor pipelines.
[Blade masks can be constructed](construction.md) from explicit blade IDs,
string expressions, grade filters, or directly from multivectors via
`from_mv` and `from_array`.  [Properties include](properties-and-ops.md) O(1)
membership testing (`bid in mask`), O(1) position lookup (`index()`), blade
name listing (`names()`), and set operations (`union`, `intersection`).
[How blade masks are used in practice](usage.md) across `MVTensor`,
`MVMatrix`, `MVProductMatrix`, and the solver functions is described in the
usage guide.  The [inverse blade mask](inverse-blade-mask.md) page covers the
mathematical derivation of `inverse_blade_mask` and `product_blade_mask`
using bitmask algebra.

```python
from pytanga import BladeMask
```

Every `BladeMask` is tied to one `Algebra` — operations between masks from
different algebras are rejected.  Mask compatibility (same algebra, same
blade IDs) is enforced at every point where two axes are aligned.

## Reference

| Topic | Guide |
|-------|-------|
| Construction — from IDs, strings, grades, MVs, arrays | [Construction](construction.md) |
| Properties, membership, indexing, set operations | [Properties & Operations](properties-and-ops.md) |
| How BladeMasks are used in MVTensor, MVMatrix, MVProductMatrix, and solvers | [Usage in Pipelines](usage.md) |
| Mathematical derivation of `inverse_blade_mask` and `product_blade_mask` | [Inverse Blade Mask](inverse-blade-mask.md) |

## Quick start

```python
from pytanga import Algebra, BladeMask
from pytanga.basis import BasisE3

alg = BasisE3()

# All 8 blades
full = BladeMask.full(alg)

# Even sub‑algebra (scalar + bivectors)
even = BladeMask(alg, grades=[0, 2])

# Non‑zero blades of a multivector
a_mask = BladeMask.from_mv(alg, mv)

# Union of masks across multiple MVs
combined = BladeMask.from_array(alg, [mv1, mv2, mv3])
```
