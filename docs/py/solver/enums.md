# Enums & Coercion

The solver functions accept `EProduct` and `EInv` enum values to control
which GA product is used and whether involutions (reverse, conjugate) are
applied to operands.  They also accept scalars and strings in place of `MV`
instances.

## `EProduct` — choosing the GA operation

```python
from pytanga.enums import EProduct
```

| Value | Operation | Description |
|-------|-----------|-------------|
| `EProduct.GP` | Geometric product (`*`) | The full GA product |
| `EProduct.IP` | Inner product (`|`) | The contraction / inner product |
| `EProduct.OP` | Outer product (`^`) | The wedge / outer product |

Solvers and matrix functions accept a `product` keyword:

```python
from pytanga.solver.solve import solve

X = solve(A, Y, product='op', algebra=alg)

from pytanga.matrix.product import product_matrix
M = product_matrix(A, b_mask=b_mask, c_mask=c_mask, product=EProduct.IP)
```

The default is `EProduct.GP`.

## `EInv` — operand involutions

```python
from pytanga.enums import EInv
```

| Value | Sign pattern | What it does |
|-------|-------------|--------------|
| `EInv.ID` | None | Identity (default) |
| `EInv.REV` | `(-1)^(k(k-1)/2)` | Reverse: negates grades 2, 3 mod 4 |
| `EInv.CONJ` | `(-1)^(k(k-1)/2 + r)` | Clifford conjugate: reverse + negative‑metric sign |

`EInv` is a `StrEnum`, so `EInv.REV == "rev"` is `True`.

Both the solvers and `product_matrix` accept `left_inv` and `right_inv`:

```python
from pytanga.enums import EInv
from pytanga.solver.solve import solve

# Solve rev(A) * X = C
X = solve(A, C, left_inv=EInv.REV, algebra=alg)

# Build product matrix with rev on A, conj on X
M = product_matrix(A, b_mask=b_mask, c_mask=c_mask,
                   left_inv=EInv.REV, right_inv=EInv.CONJ)
```

**Default**: both `left_inv` and `right_inv` default to `EInv.ID`.

## Input coercion (MVLike)

Every solver function that expects a multivector also accepts:

| Input type | Behaviour |
|------------|-----------|
| `MV` | Used directly |
| `int` / `float` | Coerced to the scalar MV |
| `str` | Parsed with the same grammar as `Algebra("...")` |
| `list[MV]` | Batch of MVs (for `solve_lsq`, `product_matrix`) |

```python
solve(A, 1.0, algebra=alg)              # 1.0 → scalar MV
solve(A, "e1", algebra=alg)             # "e1" → MV with e1=1
solve(A, "2e1 - e2", algebra=alg)       # parsed expression