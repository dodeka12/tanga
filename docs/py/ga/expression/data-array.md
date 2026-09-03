# DataArray

`pytanga.expression.DataArray` is the labeled data container for the expression
system. It wraps a NumPy array (or a list of multivectors) together with one
axis spec per dimension:

- a [`BladeMask`](../blade-mask/index.md) marks a **blade axis** — the
  coefficients along that axis are the multivector components for that mask;
- a `str` names a **counting axis** — a `None`-mask batch/index axis.

This single type covers all non-scalar bindings of `Expression.__call__`:

- bind a *variable* to a `DataArray` (the blade axis is matched to the
  variable's mask);
- reduce a *counting axis* with a `DataArray` (all-counting-axis data).

A runnable tour of these cases lives in
`py/examples/expression_dataarray.py`.

## Construction

```python
import numpy as np
from pytanga import DataArray
from pytanga.basis import BasisN3
from pytanga.blade_mask import BladeMask

N3 = BasisN3()
point_mask = BladeMask(N3, [N3.E1, N3.E2, N3.E3])

# NumPy array: one blade axis + one counting axis.
points = DataArray(np.random.rand(100, 3), masks=("pnt_idx", point_mask))

# A list of MVs is converted automatically (exactly one BladeMask + one name).
mv_points = DataArray(
    [N3({N3.E1: 1.0, N3.E2: 2.0, N3.E3: 3.0})],
    masks=("pnt_idx", point_mask),
)

# Pure scalar fields: every axis is a counting axis.
scalars = DataArray(np.random.rand(100), masks=("n",))
scalars2d = DataArray(np.random.rand(100, 2), masks=("n", "m"))
```

The blade axis may come first or last; `DataArray` reorders it to match the
`BladeMask` position in `masks`.

## Variable binding

Pass a `DataArray` for a variable. The single blade axis must match the
variable's mask; every counting axis is kept element-wise and shared across the
variable's occurrences.

```python
bi_var = Variable("bi_var", BladeMask(N3, [N3.E12, N3.E13, N3.E23]))
x_pnt = Variable("x_pnt", point_mask)

expr = x_pnt ^ (bi_var | x_pnt)
contract = expr(x_pnt=points)   # still over bi_var, plus a "pnt_idx" axis
```

`contract` is an `Expression` over `bi_var` with one counting axis named
`"pnt_idx"`.

## Reducing a counting axis

A counting axis is reduced by naming it as a keyword.

### Sum (1-D sugar)

A raw 1-D array sums the axis away:

```python
scalar_contract = contract(pnt_idx=np.random.rand(100))
```

A 1-D `DataArray` behaves the same; its single axis is the binding key, so the
name does not need to match:

```python
scalar_contract = contract(pnt_idx=DataArray(np.random.rand(100), masks=("n",)))
```

### Multiply and keep

End the axis name with `_` (or use the `"_"` marker) to multiply element-wise
and keep the axis instead of summing it:

```python
kept = contract(pnt_idx=DataArray(scalars, masks=("_")))
# or equivalently: masks=("pnt_idx_",)
```

### Explicit sum marker

`"*"` is the explicit sum marker for the binding key:

```python
summed = contract(pnt_idx=DataArray(scalars, masks=("*",)))
```

### Keep other axes

For multi-axis scalar data, mark the binding key with `"_"`/`"*"` (or its name)
and the remaining axes become new named counting dimensions:

```python
weighted = contract(pnt_idx=DataArray(scalars2d, masks=("pnt_idx", "group_idx")))
```

This sums over `"pnt_idx"` and keeps a new `"group_idx"` axis. Using `"_"` as
the first spec instead multiplies over `"pnt_idx"` while still keeping
`"group_idx"`.

## Renaming axes

```python
renamed = data.rename_axis("n", "pnt_idx")   # returns a new DataArray
data(n="pnt_idx")                             # renames in place, returns data
```

This is useful when a scalar field is stored with a generic name (`"n"`) but the
expression's counting axis has a specific name (`"pnt_idx"`).

## Rules of thumb

- **One blade axis** for variable binding — it must equal the variable's mask.
- **All counting axes** for reduction — exactly one spec names/marks the binding
  key; the others are kept as new named dimensions.
- Counting-axis names must be unique, and a `DataArray` rejects more than one
  `"_"`/`"*"` marker.
- A raw 1-D array is a sum-only shorthand for the single-axis case.
