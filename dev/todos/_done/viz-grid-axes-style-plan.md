# Viz: GridStyle & AxesStyle Plan

**Date:** 13 August 2026

Add dedicated style classes (`GridStyle`, `AxesStyle`) for the `Grid` and
`Axis` scene objects, with per-kind canonical defaults — consistent with all
other object types. `Grid` / `Axes2D` / `Axes3D` / `Axis` keep only their
structural "shape" fields; visual properties (color, opacity, line thickness)
are set via `add(..., style=...)` and the `default_styles` registry.

---

## 1. Style classes — `py/pytanga/viz/_styles/_entity_styles.py`

Add two dataclasses (mirroring the existing `PointPathStyle` pattern):

```python
@dataclass
class GridStyle(VizStyle):
    """Visual style for :class:`~pytanga.viz.Grid`."""
    color: str | None = None
    opacity: float | None = None
    line_thickness: float | None = None

    def to_dict(self) -> dict[str, Any]:
        # emit style_type + non-None fields (color, opacity, line_thickness)

@dataclass
class AxesStyle(VizStyle):
    """Visual style for :class:`~pytanga.viz.Axis` (and Axes2D/Axes3D)."""
    color: str | None = None
    opacity: float | None = None
    line_thickness: float | None = None

    def to_dict(self) -> dict[str, Any]:
        # same shape as GridStyle
```

## 2. Register styles — `py/pytanga/viz/_styles/__init__.py`

- Import `GridStyle`, `AxesStyle` from `._entity_styles`.
- Add both to the `ObjVizStyle` type alias union.
- Add canonical defaults to `_DEFAULT_STYLE_FOR_KIND`:
  - `"Grid": GridStyle(color="#555555", opacity=0.5, line_thickness=0.02)`
  - `"Axis": AxesStyle(color="#888888", opacity=0.9, line_thickness=0.03)`
  - (Values match current `grid.js` / `axis.js` fallbacks and existing
    serializer builtins, so default rendering is unchanged.)

## 3. Kind key mapping — `py/pytanga/viz/_style_dict.py`

Extend `_kind_to_key`:
- `"grid" -> "Grid"`
- `"axis" -> "Axis"`

This wires up `set_default_color("grid", ...)` / `set_default_color("axis", ...)`.

## 4. Public exports — `py/pytanga/viz/__init__.py`

Import and add `GridStyle`, `AxesStyle` to `__all__`.

## 5. Serializer

No change required. `_serialize_grid` / `_serialize_axis` already call
`_apply_defaults(...)`, which resolves the canonical `GridStyle`/`AxesStyle`
from `styles_map`, overlays `color`/`opacity` into flat fields, and mirrors
`line_thickness` into the merged `style` dict — so per-entity
`color`, `opacity`, and `style` flow to the frontend automatically.

## 6. Frontend — `py/pytanga/viz/templates/renderers/grid.js`

Optional: read `line_thickness` via `styleParam` for consistency. Note that
`THREE.Line` thickness is capped at ~1px on most platforms; color and opacity
work fully. (glTF already derives tick/line sizing from `line_thickness`.)

## 7. Tests — `py/tests/viz/test_scene_session.py`

- `GridStyle()` / `AxesStyle()` default to `None` fields; `to_dict()` returns `style_type` only.
- `default_styles["Grid"]` and `default_styles["Axis"]` are instances with canonical color/opacity/line_thickness.
- `serialize_entity(Grid(...), style=GridStyle(color="#ff0000"))` → `color == "#ff0000"`.
- `viz.default_styles.merge("Grid", GridStyle(color="#00ff00"))` works.
- `set_default_color("grid", ...)` updates `default_styles["Grid"].color`.

## 8. Docs

- `docs/py/viz/axes-grid.md` — document `GridStyle`/`AxesStyle`.
- `docs/py/viz/styles.md` — add `GridStyle`/`AxesStyle` to the per-kind style table.

## 9. Example

Update one demo (e.g. `py/examples/viz/demo_camera_axes_grid_2d.py`) to show
`style=GridStyle(color=...)` / `style=AxesStyle(...)`.

## 10. Verification

- `uv run pytest py/tests/viz -q`
- `python -m py_compile` on all touched Python files.