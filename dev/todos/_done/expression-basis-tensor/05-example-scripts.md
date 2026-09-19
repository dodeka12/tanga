# Phase 5 — Example scripts

## Goal

Add runnable example scripts under `py/examples/` that demonstrate the new
features end-to-end: the `BladeMask` named basis and the public
`Expression.get_tensor()` / `AffineExpression.get_tensor()` (including the
`TwistBivector` 6-DOF case).  Follow `dev/workflows/example-docs.md` (license +
docstring with one-line description, `Run with:`, `Keywords:` line) and regenerate
the example docs.

## Files

- New: `py/examples/ga/blade_mask/named_basis.py`
- New: `py/examples/ga/expression/tensor_named_basis.py`

## Steps

- [x] **5.1 — `BladeMask` named-basis example**
  - `py/examples/ga/blade_mask/named_basis.py`: show
    (1) `BladeMask(N3, grades=[1]).basis_names` → `e1, e2, e3, einf, eo`,
    (2) `BladeMask(N3, "e1 + einf").ids == [1, 8, 16]` (composed-name parsing),
    (3) `basis_vectors` / `basis_matrix` for the reduced
    `e1∧e∞, e2∧e∞, e3∧e∞` directions over the twist mask,
    (4) `mask_for(N3, TwistBivector).basis_names` → the 6 physical DOF names.
  - Header per `dev/workflows/example-docs.md`.

- [x] **5.2 — expression `get_tensor()` / `get_array()` example**
  - `py/examples/ga/expression/tensor_named_basis.py`: build a twist-variable
    expression, read its raw tensor with `get_tensor()`, then call
    `get_tensor().get_array()` with the default variable basis to get a 6-column
    matrix, and with an explicit `out_basis` (6 Euclidean directions) to get a
    6×6 matrix; print shapes + a couple of values.
  - Header per `dev/workflows/example-docs.md`.

- [x] **5.3 — regenerate example docs**
  - Run `uv run python tools/generate-example-docs.py` (and
    `uv run python tools/generate-example-docs.py --check`) so both examples appear
    in the docs gallery and nav.

## Validation

`uv run python py/examples/ga/blade_mask/named_basis.py && uv run python py/examples/ga/expression/tensor_named_basis.py && uv run python tools/generate-example-docs.py --check`

## Notes

- Keywords should be short (3–8) and task-oriented, e.g. `BladeMask, Basis,
  N3, conformal` and `expressions, tensor, TwistBivector, N3`.
- Example scripts are also covered by `ty` (annotate everything) and `ruff ANN`
  per `docs/dev/architecture/typing-and-annotations.md`.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
