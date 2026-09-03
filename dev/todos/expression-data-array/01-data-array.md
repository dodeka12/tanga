# Phase 1 — `DataArray` class

## Goal

Add a public `DataArray` data container in the tensor layer and export it. It
holds a NumPy array plus a per-axis spec (`BladeMask` for a blade axis, `str`
for a counting-axis name), supports construction from numpy arrays and from
lists of `MV`/scalars, and provides `rename_axis` / in-place `__call__` renaming.
This phase is purely additive; the expression system is untouched.

## Files

- New: `py/pytanga/expression/_data_array.py`
- Edit: `py/pytanga/expression/__init__.py`
- Edit: `py/pytanga/__init__.py`
- New: `py/tests/expression/test_data_array.py`

## Steps

- [x] **1.1 — Implement `DataArray`**
  - In `_data_array.py`, add `class DataArray` per the README contract with
    `__slots__ = ("_array", "_masks")`.
  - `__init__(array, masks)`:
    - If `array` is a `list`/`tuple`, detect whether its elements are `MV` (use
      the first element for a non-empty sequence) → list-of-MVs path; otherwise
      treat as scalars via `np.asarray`.
    - Validate `masks` is a sequence of `BladeMask | str` with `len(masks) ==
      ndim`; reject duplicate `str` names; reject more than one `_`/`*` marker.
    - For a list of MVs: require exactly one `BladeMask` and one `str`; convert
      with `to_tensor(list(mvs), mask=blade_mask)` and move the blade axis to the
      position of the `BladeMask` in `masks` (transpose when the `str` comes
      first).
  - Add `array`, `masks`, `ndim`, `shape` properties and `__repr__`.

- [x] **1.2 — Add renaming**
  - `rename_axis(old, new) -> DataArray`: return a new `DataArray` with the
    matching counting-axis `str` replaced by `new`; raise `ValueError` if `old`
    is not a `str` spec or `new` is already present.
  - `__call__(**renames) -> DataArray`: apply each `old -> new` rename to
    `self._masks` in place and return `self` (same validation as `rename_axis`).

- [x] **1.3 — Export**
  - Export `DataArray` from `py/pytanga/expression/__init__.py` (add to `__all__`).
  - Export `DataArray` from `py/pytanga/__init__.py` (import + `__all__`).

- [x] **1.4 — Add tests**
  - `test_data_array.py`: numpy construction (scalar 1-D/2-D, point data),
    list-of-MVs construction in both axis orders, scalar-list construction,
    `rename_axis` (new object, old unchanged), in-place `__call__`, and error
    cases (bad spec type, length mismatch, duplicate names, two markers, list of
    MVs with the wrong number of blade axes).

## Validation

`uv run pytest py/tests/tensor/test_data_array.py -q`

## Notes

- Reuse `to_tensor`/`BladeMask` from the tensor layer; do not touch
  `Expression`/`AffineExpression` yet.
- `BladeMask` specs are instances (e.g. `point_mask`), not `BladeMask()`.
