# Blade Mask Pipeline

Every solver call internally determines three `BladeMask` instances that
define the dimensions of the linear system.  This page describes the
pipeline and the helper functions you can call directly for step‑by‑step
solving.

## The three masks

For an equation `A ∘ X = Y`:

| Mask | Source | Meaning |
|------|--------|---------|
| `a_mask` | Non‑zero blades of A | Which blades the known operand occupies |
| `c_mask` | Non‑zero blades of Y (or `product_blade_mask` output) | Which blades the result occupies |
| `b_mask` | `inverse_blade_mask(a_mask, c_mask)` | The maximal subspace X can inhabit |

The system is square when `|c_mask| == |b_mask|`, and solvable with `solve`.
When `|c_mask| > |b_mask|` (overdetermined), use `solve_lsq`.

## Extracting non‑zero blades

```python
from pytanga import BladeMask

a_mask = BladeMask(mv)                         # non‑zero blades of an MV
```

This is how the solvers determine which blades the known operand A and the
result Y occupy.

```python
A = alg({"e1": 1.0, "e2": -2.0, 0: 0.5})
a_mask = BladeMask(A)                          # ids: {0, 1, 2}
```

## `product_blade_mask` — predict the output subspace

Given the known operand A and the unknown X's subspace `b_mask`, predict
which blades can appear in the result C:

```python
from pytanga.blade_mask.predict import product_blade_mask

c_mask = product_blade_mask(a_mask, b_mask)
c_mask = product_blade_mask(a_mask, b_mask,
                            product='gp',      # 'gp' | 'ip' | 'op'
                            left=True)          # A ∘ X vs X ∘ A
```

When `b_mask` is not provided to the solvers, they iterate `product_blade_mask`
to find a subspace where the system is square.

```python
# Find all blades reachable from vectors by repeated multiplication with A
a_mask = BladeMask(A)
b_mask = BladeMask(alg, grades=[1])            # start with vectors
c_mask = product_blade_mask(a_mask, b_mask)    # one step
# May need multiple iterations for closed subspace
```

## `inverse_blade_mask` — predict the unknown's subspace

Given A's blade mask and the desired output mask, compute the **maximal**
subspace X can live in:

```python
from pytanga.blade_mask.predict import inverse_blade_mask

b_mask = inverse_blade_mask(a_mask, c_mask)
b_mask = inverse_blade_mask(a_mask, c_mask,
                             product='gp',
                             left=True)
```

This is the "inverse problem": given `A` and `C`, what are the possible
blades of `X`?  The high‑level solvers call this automatically when the user
does not provide an explicit `b_mask`.

For the mathematical derivation, see [Inverse Blade Mask](../blade-mask/inverse-blade-mask.md).

## Automatic mask derivation in solvers

When you call `solve(A, Y, algebra=alg)` without specifying masks, the
pipeline is:

```
a_mask = BladeMask(A)
c_mask = BladeMask(Y)
b_mask = inverse_blade_mask(a_mask, c_mask)
```

If the resulting system is not square, the solver iterates `product_blade_mask`
to grow `c_mask` until it is.

## Manual control example

For educational purposes or debugging, you can run the pipeline step by step:

```python
from pytanga import BladeMask
from pytanga.blade_mask.predict import inverse_blade_mask, product_blade_mask
from pytanga.matrix.product import product_matrix
from pytanga.matrix.convert import to_matrix, from_matrix
from pytanga.matrix import MVMatrix
import numpy as np

A = alg({"e1": 1.0, "e2": -2.0, 0: 0.5})

# Step 1: determine blade masks
a_mask = BladeMask(A)
c_mask = product_blade_mask(a_mask, BladeMask.full(alg))
b_mask = inverse_blade_mask(a_mask, c_mask)

# Step 2: build the product matrix
M = product_matrix(A, a_mask=a_mask, b_mask=b_mask, c_mask=b_mask)
# M.data[0] is the (|b| × |b|) matrix

# Step 3: build the RHS
Y_vec = to_matrix(alg(1.0), mask=M.c_mask)

# Step 4: solve
X_arr = np.linalg.solve(M.data[0], Y_vec.data)
X = from_matrix(MVMatrix(X_arr, M.b_mask))

print(X)                                      # the solution MV