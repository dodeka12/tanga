# Phase 1 — Remove wireframe parameters from thick-line styles

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture. If this
> work introduces or changes architecture, update the developer docs.

## Goal

Styles whose renderer draws with a screen-space fat line (`makeFatLine`) must not
expose wireframe parameters (a wireframe overlay only makes sense on a solid
surface). Remove them from `LineStyle`, and confirm the other thick-line styles
are already clean.

## Files

- Edit: `py/pytanga/viz/_styles/_entity_styles.py`
- Edit: `py/tests/viz/test_viz_styles.py`, `py/tests/viz/test_serializer.py`
  (only if they assert Line wireframe fields)

## Steps

- [x] **1.1 — Remove wireframe fields from `LineStyle`.**
  - Drop `wireframe`, `wireframe_dash`, `wireframe_color`, `wireframe_opacity`
    from the dataclass, its `to_dict()`, and its docstring.
- [x] **1.2 — Keep wireframe on the solid-cylinder variant.**
  - `CylinderLineStyle(LineStyle)` renders a solid `CylinderGeometry` (a surface),
    where wireframe is legitimate. Re-declare the four wireframe fields on
    `CylinderLineStyle` (and its `to_dict()`), so the removal in 1.1 does not
    silently strip a valid option. Note: `line.js`'s cylinder branch does not
    currently render wireframe — this phase only keeps the field contract; wiring
    the overlay is out of scope (record if it should be added later).
- [x] **1.3 — Audit remaining thick-line styles.**
  - Confirm these are already wireframe-free and need no change:
    `DirectionStyle`, `PointPathStyle`, `GridStyle`, `AxisStyle`. Document the
    audit result in the phase notes.
- [x] **1.4 — Update tests.**
  - Adjust any test that asserts `LineStyle` wireframe keys; add a test that
    `LineStyle.to_dict()` omits wireframe and `CylinderLineStyle` still carries it.

## Validation

`uv run pytest py/tests/viz/test_viz_styles.py py/tests/viz/test_serializer.py -q`

## Notes

- `EllipseStyle`'s wireframe removal happens in Phase 3 (it becomes a thick-line
  ellipse). `Arc` is a solid torus and `Circle` is a tube, so their wireframe is
  legitimate and stays.
- Audit result: `DirectionStyle` (`color`/`opacity`/`length`), `PointPathStyle`
  (`color`/`opacity`/`line_thickness`), `GridStyle` (`color`/`opacity`/
  `line_thickness`) and `AxisStyle` (`color`/`opacity`/`line_thickness` +
  label/value styles) are already wireframe-free — no change needed.
