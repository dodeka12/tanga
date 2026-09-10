# Changes since version 1.16.0 (1.17.0-rc3)

## New Features

- **`DataArray` data container** — bind variables and reduce counting axes with a
  labeled array: `DataArray(array, masks=(...))` accepts NumPy arrays or lists of
  MVs, with `BladeMask`/`str` axis specs, and supports `rename_axis` / in-place
  `__call__` renaming.
- **Counting-axis reduction** — a counting axis introduced by a binding can be
  summed away with `expr(pnt_idx=scalars)`, multiplied element-wise and kept with
  `DataArray(..., masks=("_",))`, or partially reduced with `"_"`/`"*"` markers
  while keeping other axes as new named dimensions.
- **`RndMV` and fixed components in random generators** — the geometry random
  system now generates arbitrary multivectors via `RndMV(mask, spec)`, and
  `RndPoint`/`RndDirection`/`RndMV` accept plain fixed values as well as
  `Uniform`/`Normal`/`Constant` distributions.

## Breaking Changes

- **Removed legacy binding forms** — `Expression.__call__` /
  `AffineExpression.__call__` now accept only a single `MV`/scalar, a
  `DataArray`, or (for counting-axis reduction) a raw 1-D array. The
  `list`/`tuple`-of-MVs, `(label, [mvs])`, plain `MVTensor`, and `(array, specs)`
  tuple binding shapes are removed; use `DataArray` instead.
- **Removed `pytanga.random_mv`** — the module-level random multivector function
  is gone; use `pytanga.geometry.RndMV` (or `Geometry(...)(RndMV(...))`) for
  random multivectors. `pytanga.random_mask` is unchanged.

## Refactor

- **Type hints across the expression and tensor subsystems** — every class,
  function, and method in `py/pytanga/expression/` and `py/pytanga/tensor/` now
  has parameter and return type annotations.

