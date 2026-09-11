# Phase 2 — Style classes + canonical defaults

## Goal

Add `CylinderStyle` and `ArcStyle` to the per-kind style hierarchy, register
canonical defaults, and export them from `pytanga.viz`. Both follow the
wireframe-capable pattern of `SphereStyle` / `CircleStyle`.

## Steps

- [x] **2.1 — `py/pytanga/viz/_styles/_entity_styles.py`**
  - `CylinderStyle(VizStyle)` with fields `color`, `opacity`, `wireframe`,
    `wireframe_dash`, `wireframe_color`, `wireframe_opacity` (all default
    `None`); `to_dict()` returns `{"style_type": "CylinderStyle", …}`.
  - `ArcStyle(VizStyle)` with the same six fields; `to_dict()` returns
    `{"style_type": "ArcStyle", …}`.
  - Wireframe fields serialize like `SphereStyle` (`wireframe_dash` →
    `dash.to_dict()`).

- [x] **2.2 — `py/pytanga/viz/_styles/__init__.py`**
  - Import `CylinderStyle`, `ArcStyle` from `_entity_styles`.
  - Add both to the `ObjVizStyle` union.
  - Add canonical defaults to `_DEFAULT_STYLE_FOR_KIND`:
    - `"Cylinder": CylinderStyle(color="#44aaff", opacity=0.9)`.
    - `"Arc": ArcStyle(color="#ffcc44", opacity=0.9)`.
  - Extend the `_default_style_for` annotation with `Cylinder` / `Arc`.

- [x] **2.3 — `py/pytanga/viz/_style_dict.py`**
  - Add `"Cylinder"` / `"Arc"` to the `kinds` list in
    `_make_default_label_styles`.
  - Add `"cylinder": "Cylinder"` / `"arc": "Arc"` to the `_kind_to_key` mapping
    (so `set_default_color("cylinder", …)` works).
  - Add `"Cylinder": None` / `"Arc": None` to `_make_default_tex_label_styles`.

- [x] **2.4 — Export from `py/pytanga/viz/__init__.py`**
  - Import `CylinderStyle`, `ArcStyle` from `._styles`; add both to `__all__`.

- [x] **2.5 — Unit tests (extend `py/tests/viz/test_viz_styles.py`)**
  - `"Cylinder"` and `"Arc"` are present in `make_styles().kind` with non-`None`
    `color`.
  - `to_dict()` returns the right `style_type` and omits unset fields.
  - Class-key access: `viz.styles[Cylinder]` ⇄ `viz.styles["Cylinder"]`
    (and the same for `Arc`).

- [x] **2.6 — Validate**
  - `uv run pytest py/tests/viz/test_viz_styles.py -q`.

## Validation

`uv run pytest py/tests/viz/test_viz_styles.py -q`

## Notes

- `length`/`radius` (Cylinder) and `radius`/`tubeRadius`/`angle`/`arrow` (Arc)
  are **content**, not style, so they stay out of the style classes — only
  appearance (color/opacity/wireframe) lives here.
- Canonical colors are placeholders; adjust in the docs/changelog phase if the
  team prefers different defaults.
