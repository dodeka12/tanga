# Phase 4 — `ActRectangle2D`/`ActEllipse` bodies carry the basis

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (the active-object
> composite recipe).  This stays inside the existing `ActiveObject` composite
> recipe; no architecture change.

## Goal

Make the active shape bodies store the plane basis (`dir_u`/`dir_v`) and, for
`ActEllipse`, the scalar `angle`, so the rendered body and the handles share one
frame on any plane (this is the Finding-1 body/handle fix at the `Act*` level).

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/tests/viz/test_act_rectangle2d.py`
- Edit: `py/tests/viz/test_act_ellipse.py`

## Steps

- [x] **4.1 — `ActRectangle2D` body basis.**
  - In every `Rectangle2D(...)` call — constructor (`:1198`), `_resize_corner`
    (`:1416`), `_translate_by` (`:1435`), `_rotate_to` (`:1449`) — pass
    `dir_u=self._u0, dir_v=self._v0` (keep `normal=self._normal`,
    `angle=self._angle`).  Add a small `_make_rect(center, size)` helper to avoid
    the repetition.

- [x] **4.2 — `ActEllipse` scalar angle.**
  - In `_build_ellipse` (`:1655`) pass `dir_u=self._u0, dir_v=self._v0,
    angle=self._angle` (instead of the baked `dir_u=self._dir_u(),
    dir_v=self._dir_v()`).

- [x] **4.3 — Tests.**
  - `test_act_rectangle2d.py` / `test_act_ellipse.py`: with a tilted `normal`
    (e.g. `Direction(-0.009,-0.009,-1.0)`) assert `entity.dir_u`/`dir_v` equal
    `_u0`/`_v0`, `entity.angle` equals the internal angle, and `entity.normal`
    is preserved; keep the existing flat `normal=+z` tests green.

## Validation

`uv run pytest py/tests/viz/test_act_rectangle2d.py py/tests/viz/test_act_ellipse.py -q`

## Notes

- The handles already use `_dir_u()/`_dir_v()` from `_u0`/`_v0`; once the body
  carries the same basis, Phase 2's `_decompose` makes body and handles agree.
- `ActCircle` is unchanged (its radius handle already uses `_u0`; the body is
  symmetric).
