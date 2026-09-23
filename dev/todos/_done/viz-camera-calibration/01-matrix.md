# Phase 1 — `Matrix` + `MatrixProvider`

## Goal

A typed, plain numeric matrix (`pytanga.geometry.Matrix`) and a runtime-checkable
`MatrixProvider` Protocol, wired into the scene graph so `set_transform`/`apply_transform` accept any `to_matrix()` provider.

## Files

- New: `py/pytanga/geometry/matrix.py`
- New: `py/tests/geometry/test_matrix.py`
- Edit: `py/pytanga/geometry/__init__.py` (export `Matrix`, `MatrixProvider`)
- Edit: `py/pytanga/viz/_nodes.py` (`Transform.to_matrix`, `_coerce_transform_matrix`)
- Edit: `py/pytanga/viz/_types.py` (`TransformInput` accepts `MatrixProvider`)

## Steps

- [x] **1.1 — `Matrix` class**
  - square numpy, column-vector; `to_matrix()`, `to_numpy()`, `__array__`, `.T`, `inverse()`, `det()`, `is_rotation()`, `__matmul__` (Matrix/Point/Direction/ndarray), `__eq__`.
  - classmethods `identity`, `translation`, `rotation`, `scale`, `from_axes`.
- [x] **1.2 — `MatrixProvider` Protocol**
  - `@runtime_checkable` Protocol with `to_matrix() -> np.ndarray`.
- [x] **1.3 — wire into scene graph**
  - `Transform.to_matrix()` alias for `matrix()`; `_coerce_transform_matrix` accepts `MatrixProvider` first; `TransformInput` widened.
- [x] **1.4 — tests**

## Validation

`uv run pytest py/tests/geometry/test_matrix.py -q && uv run ruff check . && uv run ty check`
