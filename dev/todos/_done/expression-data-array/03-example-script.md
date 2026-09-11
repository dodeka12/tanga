# Phase 3 — example script

## Goal

Add a runnable example under `py/examples/` that demonstrates expressions,
variables, and `DataArray`s, covering the use cases from
`_input/test_expression_1.py` (product operators + the `+`/`^`/`|` precedence
gotcha) and `_input/test_expression_2.py` (point arrays, scalar arrays, counting
axes, and reductions).

## Files

- New: `py/examples/expression_dataarray.py`

## Steps

- [x] **3.1 — Add the example with the docs header**
  - Create `py/examples/expression_dataarray.py` with the license header and a
    module docstring per `dev/workflows/example-docs.md`: a one-line
    `<name>.py — …` description, a `Run with:` line, and a trailing
    `Keywords:` line (e.g. `expression, variable, DataArray, geometric algebra,
    contraction`).

- [x] **3.2 — Cover the `_input/test_expression_1.py` use cases**
  - Set up `BasisN3`, `bi_mask`, `point_mask`, a `bi_var` and an `x_pnt`
    variable.
  - Show `*`/`|`/`^` with constants and variables, and evaluate with a single
    `MV`.
  - Show the precedence pitfall explicitly: the unparenthesised
    `a * (v | e3) ^ e3 + (b * (v ^ e3) | e3)` vs the parenthesised
    `(a * (v | e3) ^ e3) + (b * (v ^ e3) | e3)`.

- [x] **3.3 — Cover the `_input/test_expression_2.py` use cases with `DataArray`**
  - Build `DataArray` from a NumPy point array, from a list of MVs, and from
    1-D/2-D scalar arrays.
  - Bind `x_pnt` to a point `DataArray`, then reduce the introduced counting
    axis: raw 1-D sum sugar, `"_"` multiply/keep, `"*"` sum, the 1-D implicit
    key, and the keep-other form `("pnt_idx", "group_idx")`.
  - Show `rename_axis` and in-place `__call__` renaming.

- [x] **3.4 — Validate the example**
  - Run the script and regenerate/check the example docs.

## Validation

`uv run python py/examples/expression_dataarray.py; uv run python tools/generate-example-docs.py; uv run python tools/generate-example-docs.py --check`

## Notes

- This phase runs only after Phases 1–2 (the `DataArray` class and the unified
  binding API exist).
