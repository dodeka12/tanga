# Phase 3 — Type wiring + serializer

## Goal

Route `Cylinder` / `Arc` through `Visualizer._resolve` (viz-only pass-through)
and add serializer leaves that emit the fixed wire contract from the README.

## Steps

- [x] **3.1 — `py/pytanga/viz/_types.py`**
  - Import `Cylinder`, `Arc` and add them to the `SceneEntity` union (so
    `Visualizer._resolve` returns them unchanged instead of trying to `analyze`
    them).

- [x] **3.2 — `py/pytanga/viz/serializer.py`**
  - Import `Cylinder`, `Arc` from `pytanga.geometry.entities`.
  - Add dispatch branches in `_dispatch_entity` (before the operator section,
    alongside the other entity `isinstance` checks).
  - `_serialize_cylinder(ent, props, *, kind, styles_map)`:
    - `_apply_defaults(props, kind, {}, styles_map=styles_map)` then
      `| {"origin": [...], "axis": [...], "length": ent.length,
           "radius": _clamp_positive(ent.radius)}`.
  - `_serialize_arc(ent, props, *, kind, styles_map)`:
    - `_apply_defaults(props, kind, {}, styles_map=styles_map)` then
      `| {"origin": [...], "axis": [...], "radius": _clamp_positive(ent.radius),
           "tubeRadius": _clamp_positive(ent.tube_radius),
           "angle": ent.angle,
           "startDirection": [ent.start_direction.x, ...],
           "arrow": <resolved arrow dict or None>}`.
    - Resolve `arrow` Python-side:
      - `show_arrow=False` → `"arrow": None`.
      - `show_arrow=True` → `"arrow": {"length": eff_len, "radius": eff_rad}`,
        where `eff_len = arrow_length or 3 * tube_radius` and
        `eff_rad = arrow_radius or 2 * tube_radius`.
  - Use camelCase content keys (`tubeRadius`, `startDirection`) and keep style
    keys snake_case inside `style`, matching the README contract.

- [x] **3.3 — Unit tests (extend `py/tests/viz/test_serializer.py`)**
  - `Cylinder`: `kind == "Cylinder"`, geometry fields, `origin`/`axis` lists,
    and default style color/opacity present.
  - `Arc`: `kind == "Arc"`, `angle` in radians, `startDirection` is a 3-list and
    normalized (even when the user omitted it), `arrow is None` by default.
  - `Arc` with `show_arrow=True` and no explicit sizes → `arrow` dict equals
    `{"length": 3*tube_radius, "radius": 2*tube_radius}`; explicit sizes are
    preserved.
  - Per-call `color=` / `style=CylinderStyle(...)` overrides land in both the
    flat `color` field and the merged `style` dict.

- [x] **3.4 — Validate**
  - `uv run pytest py/tests/viz/test_serializer.py -q`.

## Validation

`uv run pytest py/tests/viz/test_serializer.py -q`

## Notes

- The serializer is the single source of truth for the wire shape; Phase 4/5
  renderers read exactly the keys emitted here.
- Do not add `Cylinder`/`Arc` to `serialize_entity`'s `Entity` import list —
  they are dispatched by `isinstance` on the concrete classes, not the union.
