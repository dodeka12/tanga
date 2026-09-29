# Phase 3 — `ActEllipse`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If this
> work introduces or changes architecture, update the developer docs.

## Goal

Add `ActEllipse`, an active `Ellipse` with two radius handles, a translate
handle, and a rotate handle.  Rotation is encoded in `Ellipse.dir_u`/`dir_v`
(verified: `_entity_decompose` maps `dir_u` + `normal` to a quaternion).

## Files

- Edit: `py/pytanga/viz/_active.py` (new `ActEllipse`)
- Edit: `py/pytanga/viz/__init__.py` (export `ActEllipse`)
- New: `py/tests/viz/test_act_ellipse.py`

## Steps

- [x] **3.1 — Model.**
  - `ActEllipse(center=None, radius_u=1.0, radius_v=0.5, *, angle=0.0,
    show_translate_handle=True, show_rotate_handle=True, handle_style=None,
    act_style=None, on_radius_drag=None, on_translate=None, on_rotate=None,
    on_change=None, on_click=None)`; inherit `_ActWithHandles`.
  - `entity` property returns an `Ellipse` with `normal=+z`,
    `dir_u=(cos angle, sin angle, 0)`, `dir_v=(-sin angle, cos angle, 0)`.
- [x] **3.2 — Handles.**
  - Spawn radius handles at `center ± radius_u·dir_u` and `center ± radius_v·dir_v`
    (take the +u/+v ends as the draggable radius handles), a translate handle at
    `center`, and a rotate handle offset from the rim along `dir_u` when
    `show_rotate_handle=True`.
- [x] **3.3 — Handlers.**
  - Radius drag → recompute `radius_u`/`radius_v` from the handle distance to
    centre (clamped ≥ 0); translate → move centre; rotate → `atan2` of
    `(handle - centre)` against `dir_u` updates `angle`.
  - `_commit()`: update body, refresh handle positions, flush, fire
    `on_change(Ellipse)`.
- [x] **3.4 — Export.**
  - Add `ActEllipse` to `py/pytanga/viz/__init__.py` (import + `__all__`).
- [x] **3.5 — Tests.**
  - `test_act_ellipse.py` (mirror `test_act_rectangle2d.py`): entity is an
    `Ellipse`; `dir_u`/`dir_v` encode `angle`; radius/translate/rotate dispatch
    update the ellipse; `on_change` fires; `remove()` removes body + handles.

## Validation

```
uv run pytest py/tests/viz/test_act_ellipse.py -q
```

## Notes

- `Ellipse` is rendered from `radiusU`/`radiusV` (serializer) and the
  decomposed `transform` (position + `dir_u` quaternion) — no serializer change
  is needed.
- `drag_anchor` for the body returns the ellipse centre so `on_click` reports it.
