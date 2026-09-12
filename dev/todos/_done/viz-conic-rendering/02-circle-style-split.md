# Phase 2 — Circle style split (tube vs thick line)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture. If this
> work introduces or changes architecture, update the developer docs.

## Goal

Rename the current tube/torus `CircleStyle` to `CylinderCircleStyle` (the default
for `Circle`), and add a new `CircleStyle` that renders the circle as a thick
line. The frontend dispatches the two by `style_type`.

## Files

- Edit: `py/pytanga/viz/_styles/_entity_styles.py`
- Edit: `py/pytanga/viz/_styles/__init__.py` (`_DEFAULT_STYLE_FOR_KIND["Circle"]`,
  `ObjVizStyle` union, exports)
- Edit: `py/pytanga/viz/__init__.py` (exports)
- Edit: `py/pytanga/viz/templates/renderers/circle.js`
- Edit: `py/tests/viz/test_viz_styles.py`, `py/tests/viz/test_imaginary_styles.py`

## Steps

- [x] **2.1 — Rename `CircleStyle` → `CylinderCircleStyle`.**
  - Keep its fields (`color`, `opacity`, `tube_radius`, wireframe…); change
    `to_dict()` `style_type` to `"CylinderCircleStyle"`. Keep `ImagCircle`
    using it (imaginary circle stays a tube).
- [x] **2.2 — Add the new thick-line `CircleStyle(VizStyle)`.**
  - Fields: `color`, `opacity`, `thickness` (line width, same name as
    `LineStyle.thickness`). `to_dict()` `style_type` = `"CircleStyle"`.
- [x] **2.3 — Update canonical defaults.**
  - `_DEFAULT_STYLE_FOR_KIND["Circle"]` = `CylinderCircleStyle(...)` (tube is the
    default); keep `ImagCircle` on `CylinderCircleStyle`.
- [x] **2.4 — Export + union.**
  - Add `CylinderCircleStyle` and `CircleStyle` to the `ObjVizStyle` union and the
    `_styles` / `viz` `__init__` exports.
- [x] **2.5 — Frontend dispatch.**
  - In `circle.js`, dispatch on `ent.style?.style_type`: `"CircleStyle"` samples
    the circle and draws it with `makeFatLine`; otherwise keep the existing torus
    path (which is `CylinderCircleStyle` by default).
- [x] **2.6 — Tests.**
  - Assert `make_styles()["Circle"]` is a `CylinderCircleStyle`, that
    `CircleStyle.to_dict()` has no wireframe, and that both styles serialize.

## Validation

`uv run pytest py/tests/viz/test_viz_styles.py py/tests/viz/test_imaginary_styles.py -q && node --input-type=module --check py/pytanga/viz/templates/renderers/circle.js`

## Notes

- `_serialize_circle` already emits `tubeRadius` (camelCase content field) and the
  style carries `tube_radius` (snake_case). Keep this existing split; the
  thick-line path only adds the `thickness` style field and does not change the
  geometry fields.
