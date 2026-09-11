# Phase 3 — Conic/Quadric3D style hierarchy

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture. If this
> work introduces or changes architecture, update the developer docs.

## Goal

Introduce `ConicStyle` as the base of every 2D conic style, and
`Quadric3DStyle` as the base of the 3D quadric styles, with the missing concrete
style classes (`HyperbolaStyle`, `ParabolaStyle`, `LinePairStyle`,
`ParallelLinePairStyle`, `ConeStyle`) and a corrected `EllipseStyle` (thick
line, no wireframe/slab).

## Files

- Edit: `py/pytanga/viz/_styles/_entity_styles.py`
- Edit: `py/pytanga/viz/_styles/__init__.py`
- Edit: `py/pytanga/viz/__init__.py`
- Edit: `py/tests/viz/test_viz_styles.py`, `py/tests/viz/test_serializer.py`

## Steps

- [x] **3.1 — `ConicStyle(VizStyle)` base.**
  - Fields `color`, `opacity`, `thickness` (line width). `to_dict()` →
    `{"style_type":"ConicStyle", ...}`.
- [x] **3.2 — `EllipseStyle(ConicStyle)`.**
  - Drop `wireframe`, `wireframe_dash`, `wireframe_color`, `wireframe_opacity`
    and the slab-`thickness`; `thickness` becomes the line width (inherited from
    `ConicStyle`). Update the docstring: 2D line ellipse (keep `normal` on the
    entity, not the style).
- [x] **3.3 — `HyperbolaStyle`/`ParabolaStyle`/`LinePairStyle`/
  `ParallelLinePairStyle` subclasses.**
  - `HyperbolaStyle(ConicStyle)` + `extent`; `ParabolaStyle(ConicStyle)` +
    `extent`; `LinePairStyle(ConicStyle)` + `length`;
    `ParallelLinePairStyle(ConicStyle)` + `length`. Each with its own `to_dict()`
    `style_type`.
- [x] **3.4 — `Quadric3DStyle(VizStyle)` base + `ConeStyle`.**
  - `Quadric3DStyle` base (solid-surface style: `color`, `opacity`, and the
    wireframe fields). Subclass `SphereStyle`, `EllipsoidStyle`, `CylinderStyle`,
    `PlaneStyle`; add `ConeStyle(Quadric3DStyle)` (no extra knobs).
- [x] **3.5 — Canonical defaults.**
  - Register `_DEFAULT_STYLE_FOR_KIND` for `Hyperbola`, `Parabola`, `LinePair`,
    `ParallelLinePair`, `Cone`. Update `Ellipse` default to a line style
    (`color`, `opacity`, `thickness`).
- [x] **3.6 — Export + union.**
  - Add all new classes to `ObjVizStyle` and the `_styles`/`viz` exports.
- [x] **3.7 — Tests.**
  - Assert the new kinds exist in `make_styles().kind`; assert `EllipseStyle`
    has no wireframe; assert the `ConicStyle`/`Quadric3DStyle` subclass
    relationships.

## Validation

`uv run pytest py/tests/viz/test_viz_styles.py py/tests/viz/test_serializer.py -q`

## Notes

- Keep `ConicStyle` instantiable (a user may pass a bare `ConicStyle`); its
  `style_type` is allowed to stay `"ConicStyle"` in the wire.
- `Circle`/`Line` already have styles and are not part of this hierarchy change
  beyond Phase 2.
