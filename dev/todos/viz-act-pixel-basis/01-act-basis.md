# Phase 1 — `Act*` accept an in-plane basis

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (the active-object
> composite recipe).  No architecture change — this extends the existing
> `ActiveObject` composite recipe with an explicit basis.

## Goal

Give `ActRectangle2D`, `ActEllipse`, and `ActCircle` an optional `dir_u`/`dir_v`
basis (default `_plane_basis(normal)`), validate it, and expose it read-only.

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/tests/viz/test_act_rectangle2d.py`
- Edit: `py/tests/viz/test_act_ellipse.py`
- Edit: `py/tests/viz/test_act_circle.py`

## Steps

- [x] **1.1 — Commit the pending `ActRectangle2D`/`ActEllipse` basis work.**
  - The `dir_u`/`dir_v` constructor params and `_resolve_basis` helper are already
    in the working tree (uncommitted).  Review them, then commit them.

- [x] **1.2 — `ActCircle` `dir_u`/`dir_v`.**
  - Add `dir_u`/`dir_v` kwargs to `ActCircle.__init__` (after `normal`); resolve
    `_normal`/`_u0`/`_v0` with `_resolve_basis(normal, dir_u, dir_v)`.

- [x] **1.3 — Orthonormal + right-handed validation.**
  - In `_resolve_basis`, after normalizing `u0`/`v0`, verify `|u0·v0| < tol` and
    `|(u0 × v0) − normal| < tol` (and that a caller-supplied `normal`, if given,
    matches `u0 × v0`); raise `ValueError` otherwise.

- [x] **1.4 — Read-only `dir_u`/`dir_v` properties.**
  - Add `@property dir_u`/`dir_v` returning the stored normalized basis on all
    three Acts.

- [x] **1.5 — Tests.**
  - Explicit basis overrides `normal` (body `dir_u`/`dir_v`/`normal` match).
  - Half-specified basis raises; non-orthonormal basis raises.
  - Default (no `dir_u`/`dir_v`) is unchanged (golden values).

## Validation

`uv run pytest py/tests/viz/test_act_rectangle2d.py py/tests/viz/test_act_ellipse.py py/tests/viz/test_act_circle.py -q`

## Notes

- `_resolve_basis` already exists (pending); this phase hardens it and adds
  `ActCircle` + the read-only properties.
