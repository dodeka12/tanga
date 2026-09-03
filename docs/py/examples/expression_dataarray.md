# Expressions, variables, and DataArray bindings

**Keywords:** expression · variable · DataArray · geometric algebra · contraction

Walk through the expression DSL: build expressions from variables and constants,
evaluate them with single multivectors, bind variables to labeled NumPy arrays
via `pytanga.DataArray`, and reduce the counting axes that such bindings
introduce.

## Run

```bash
uv run python py/examples/expression_dataarray.py
```

## Source

[`expression_dataarray.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/expression_dataarray.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""expression_dataarray.py — Expressions, variables, and DataArray bindings.

Walk through the expression DSL: build expressions from variables and constants,
evaluate them with single multivectors, bind variables to labeled NumPy arrays
via :class:`pytanga.DataArray`, and reduce the counting axes that such bindings
introduce.

Run with:  uv run python py/examples/expression_dataarray.py

Keywords: expression, variable, DataArray, geometric algebra, contraction
"""

import numpy as np

from pytanga import DataArray, Variable
from pytanga.basis import BasisN3
from pytanga.blade_mask import BladeMask


def hr(title: str) -> None:
    print(f"\n{'=' * 62}\n{title}\n{'=' * 62}")


N3 = BasisN3()
bi_mask = BladeMask(N3, [N3.E12, N3.E13, N3.E23])
point_mask = BladeMask(N3, [N3.E1, N3.E2, N3.E3])

bi_var = Variable("bi_var", bi_mask)
x_pnt = Variable("x_pnt", point_mask)

# ----------------------------------------------------------------------
# 1. Products with a single multivector (from _input/test_expression_1.py)
# ----------------------------------------------------------------------
hr("1. Products and single-multivector evaluation")

a: float = 2.0
b: float = 3.0

expr1 = a * (bi_var | N3.e3) ^ N3.e3
expr2 = b * (bi_var ^ N3.e3) | N3.e3

bi_test = N3({N3.E12: 1.0, N3.E13: 2.0, N3.E23: 3.0})
print("expr1:", expr1)
print("expr2:", expr2)
print("expr1(bi_var=bi_test) =", expr1(bi_var=bi_test))
print("expr2(bi_var=bi_test) =", expr2(bi_var=bi_test))

# Operator precedence: `^`/`|` bind more loosely than `+`, so the two terms
# must be parenthesised when summed.
unparenthesised = a * (bi_var | N3.e3) ^ N3.e3 + (b * (bi_var ^ N3.e3) | N3.e3)
parenthesised = (a * (bi_var | N3.e3) ^ N3.e3) + (b * (bi_var ^ N3.e3) | N3.e3)
print("\nunparenthesised sum:", unparenthesised(bi_var=bi_test))
print("parenthesised sum:  ", parenthesised(bi_var=bi_test))

# ----------------------------------------------------------------------
# 2. DataArray construction
# ----------------------------------------------------------------------
hr("2. DataArray construction")

points = np.random.default_rng(0).random((100, 3))
scalars = np.random.default_rng(1).random(100)
scalars2d = np.random.default_rng(2).random((100, 2))

points_data = DataArray(points, masks=("pnt_idx", point_mask))
mv_list_data = DataArray(
    [N3({N3.E1: p[0], N3.E2: p[1], N3.E3: p[2]}) for p in points[:3]],
    masks=("pnt_idx", point_mask),
)
scalar_data = DataArray(scalars, masks=("n",))
scalar2d_data = DataArray(scalars2d, masks=("n", "m"))

print("points_data :", points_data)
print("mv_list_data:", mv_list_data)
print("scalar_data :", scalar_data)
print("scalar2d_data:", scalar2d_data)

# ----------------------------------------------------------------------
# 3. Variable binding and counting-axis reduction (test_expression_2.py)
# ----------------------------------------------------------------------
hr("3. Variable binding with DataArray")

expr = x_pnt ^ (bi_var | x_pnt)
contract = expr(x_pnt=points_data)
print("contract:", contract)
print("names:", contract.names, "ndim:", contract.ndim)

bi_test = N3({N3.E12: 1.0, N3.E13: 2.0, N3.E23: 3.0})

# Sum the counting axis with a raw 1-D array (sum sugar), or a 1-D DataArray.
scalar_contract = contract(pnt_idx=scalars)
print("\nsum via raw array:", scalar_contract(bi_var=bi_test))
print("sum via 1-D DataArray:", contract(pnt_idx=scalar_data)(bi_var=bi_test))

# Multiply element-wise and keep the axis with the `_` marker.
kept = contract(pnt_idx=DataArray(scalars, masks=("_",)))
print("multiply/keep ndim:", kept.ndim, "->", len(kept(bi_var=bi_test)), "results")

# Sum one counting axis and keep another with a 2-D DataArray.
points2d = np.random.default_rng(3).random((100, 2, 3))
two_axes = expr(x_pnt=DataArray(points2d, masks=("pnt_idx", "group_idx", point_mask)))
reduced = two_axes(pnt_idx=DataArray(scalars2d, masks=("pnt_idx", "group_idx")))
print("\ncontract one / keep one:", reduced)
print("per-group results:", len(reduced(bi_var=bi_test)))

# ----------------------------------------------------------------------
# 4. Renaming counting axes
# ----------------------------------------------------------------------
hr("4. Renaming counting axes")

renamed = scalar_data.rename_axis("n", "pnt_idx")
print("rename_axis ->", renamed.masks, "| original ->", scalar_data.masks)

in_place = DataArray(scalars, masks=("n",))
in_place(n="_")
print("in-place call ->", in_place.masks, "| is self:", in_place is in_place)
````
