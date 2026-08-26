# Phase 2 — Style classes + canonical defaults (mesh + SDF)

## Goal

Add one mesh style class and one SDF style class per new entity, register
canonical defaults, and export them from `pytanga.viz`. Mesh styles follow the
wireframe-capable pattern of `SphereStyle` / `CircleStyle`; SDF styles carry only
SDF-implementable knobs.

## Files

- Modify: `py/pytanga/viz/_styles/_entity_styles.py`
- Modify: `py/pytanga/viz/_styles/_sdf_style.py`
- Modify: `py/pytanga/viz/_styles/__init__.py`
- Modify: `py/pytanga/viz/_style_dict.py`
- Modify: `py/pytanga/viz/__init__.py`
- Modify: `py/tests/viz/test_viz_styles.py`, `py/tests/viz/sdf/test_sdf_styles.py`

## Steps

- [x] **2.1 — Mesh styles (`_entity_styles.py`)**
  - Add `DiskStyle`, `PartialDiskStyle`, `BoxStyle`, `EllipsoidStyle`,
    `EllipseStyle`, `RegularPolygonStyle`, each with `color`, `opacity`,
    `wireframe`, `wireframe_dash`, `wireframe_color`, `wireframe_opacity`
    (all default `None`).
  - `DiskStyle`/`PartialDiskStyle`/`EllipseStyle`/`RegularPolygonStyle`
    additionally carry `thickness: float | None` (slab thickness; canonical
    default `0.02`).
  - `to_dict()` returns `{"style_type": "<Name>", …}` and serializes
    `wireframe_dash` like `SphereStyle`.

- [x] **2.2 — SDF styles (`_sdf_style.py`)**
  - Add `SdfDiskStyle`, `SdfPartialDiskStyle`, `SdfBoxStyle`, `SdfEllipsoidStyle`,
    `SdfEllipseStyle`, `SdfRegularPolygonStyle` (all derive from `SdfStyle`).
  - `SdfDiskStyle`/`SdfPartialDiskStyle`/`SdfEllipseStyle`/
    `SdfRegularPolygonStyle` add `thickness: float = 0.02` (serialized in
    `to_dict()`); `SdfBoxStyle`/`SdfEllipsoidStyle` add no extra knobs.
  - Extend `SDF_STYLE_BY_KIND` with the six new entity kinds.

- [x] **2.3 — `_styles/__init__.py`**
  - Import the six mesh styles and six SDF styles.
  - Add all twelve to the `ObjVizStyle` union.
  - Add canonical mesh defaults to `_DEFAULT_STYLE_FOR_KIND` (placeholder
    colors: `Disk="#ff8844"`, `PartialDisk="#ffcc44"`, `Box="#88ccff"`,
    `Ellipsoid="#ffaa00"`, `Ellipse="#ff44ff"`, `RegularPolygon="#44ffaa"`;
    `opacity=0.9`; `thickness=0.02` where applicable).
  - Extend the `_default_style_for` annotation with the new entity types.

- [x] **2.4 — `_style_dict.py`**
  - Add the six new kinds to `_make_default_label_styles`.
  - Add the six new kinds to `_make_default_tex_label_styles` (all `None`).
  - Add lower-case mappings to `_kind_to_key`.

- [x] **2.5 — Export from `viz/__init__.py`**
  - Import the six mesh styles and six SDF styles; add to `__all__`.

- [x] **2.6 — Unit tests**
  - `test_viz_styles.py`: new kinds present in `make_styles().kind` with
    non-`None` color; `to_dict()` `style_type` + omitted unset fields; class-key
    ⇄ string-key access.
  - `test_sdf_styles.py`: update the exact `SDF_STYLE_BY_KIND` assertion; each
    `Sdf*Style.to_dict()` has the right `style_type` and SDF-only keys; derived
    classes expose no `wireframe`/`texture_label`/`double_sided`.

- [x] **2.7 — Validate**
  - `uv run pytest py/tests/viz/test_viz_styles.py -q` and
    `uv run pytest py/tests/viz/sdf/test_sdf_styles.py -q`.

## Validation

`uv run pytest py/tests/viz/test_viz_styles.py py/tests/viz/sdf/test_sdf_styles.py -q`

## Notes

- `radius`/`size`/`radii`/`sides`/`normal`/`angle` are **content**, not style;
  only appearance (color/opacity/wireframe/thickness) lives in the styles.
- `thickness` is a style knob on both the mesh and SDF side so the slab stays
  consistent between the two renderers.
- Canonical colors are placeholders; adjust in the docs/changelog phase.
