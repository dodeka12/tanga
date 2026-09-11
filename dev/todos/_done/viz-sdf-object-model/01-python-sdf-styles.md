# Phase 1 — Per-entity SDF styles (`Sdf*Style`)

## Goal

Split the generic `SdfStyle` marker into **one SDF style class per entity**, each
carrying only SDF-implementable parameters (never `wireframe`/`texture_label`/
`double_sided`). The common knobs stay on the `SdfStyle` base; entity-specific
shape knobs (`thickness`, `tube_radius`, `size`) live on the derived classes.

## Files

- Modify: `py/pytanga/viz/_styles/_sdf_style.py` — add derived classes.
- Modify: `py/pytanga/viz/_styles/__init__.py` — export them.
- Modify: `py/pytanga/viz/__init__.py` — export them.
- New: `py/tests/viz/sdf/test_sdf_styles.py`.

## Steps

- [x] **1.1 — Derived classes** (`_styles/_sdf_style.py`)
  - Keep `SdfStyle` (base: `color`, `opacity`, `soft_shadows`, `max_steps`,
    `bound_padding`).
  - Add, each `to_dict()` → `{"style_type": "<Name>", ...}`:
    - `SdfSphereStyle(SdfStyle)` — no extras.
    - `SdfLineStyle(SdfStyle)` — `thickness: float = 1.0`.
    - `SdfCircleStyle(SdfStyle)` — `tube_radius: float = 0.03`.
    - `SdfPointStyle(SdfStyle)` — `size: float = 0.08`.
    - `SdfCylinderStyle(SdfStyle)` — no extras.
    - `SdfPlaneStyle(SdfStyle)` — no extras (extent is geometric on `Plane`).

- [x] **1.2 — kind→style registry**
  - A module-level map `SDF_STYLE_BY_KIND = {"Sphere": SdfSphereStyle,
    "Line": SdfLineStyle, "Circle": SdfCircleStyle, "Point": SdfPointStyle,
    "Cylinder": SdfCylinderStyle, "Plane": SdfPlaneStyle, ...}` so
    `_entity_to_sdf` (Phase 3) can default the right style when a raw entity is
    wrapped without an explicit style.

- [x] **1.3 — Exports**
  - Re-export from `_styles/__init__.py` and `py/pytanga/viz/__init__.py`
    (`from pytanga.viz import SdfLineStyle, ...`).

- [x] **1.4 — Tests** (`py/tests/viz/sdf/test_sdf_styles.py`)
  - Each class `to_dict()` has the right `style_type` + SDF-only keys.
  - `isinstance(SdfLineStyle(), SdfStyle)` is true.
  - Derived classes expose **no** `wireframe`/`texture_label`/`double_sided`
    attributes.

- [x] **1.5 — Validate**
  - `uv run pytest py/tests/viz/sdf/test_sdf_styles.py -q` and
    `uv run pytest py/tests/viz/ -q`.

## Validation

`uv run pytest py/tests/viz/ -q` (existing suite still green) +
`uv run pytest py/tests/viz/sdf/test_sdf_styles.py -q`.

## Notes

- This phase is purely additive: `SdfStyle` and the marker detection
  (`_is_sdf_styled`) are unchanged, so existing `viz.add(Sphere(...),
  style=SdfStyle(...))` keeps working.
- The derived classes are *data only* — no serializer wiring yet (that lands in
  Phases 3–4).
