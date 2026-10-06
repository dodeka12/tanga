# Labelme shape labeling (ActCircle / ActLine / point styles / labelme module / example app) — Overview

**Created:** 2026-09-28 | **Status:** Done | **Branch:** `feat/more-act-entities`

## Goal

Follow on from `dev/todos/viz-active-shape-labeling/` (already done) and turn the
image labeling example into a real **labelme** application.  In service of that:

- two new point styles — `CirclePointStyle` (outline/filled disc) and
  `IconPointStyle` (any `material:*` glyph) — used for the composite handles;
- `ActRectangle2D` rotation (it already serializes `angle`; it just can't be
  dragged into a rotation), plus a configurable minimum size;
- a dedicated `ActCircle` (center + radius) and `ActLine` (a single `Line`
  segment) active composite;
- generalized `ActPolygon` vertex editing: Ctrl+drag **any** vertex inserts a
  vertex after it; Ctrl+right-click deletes a vertex (keeping a closed polygon
  closed while ≥3 vertices remain); Ctrl+Shift+right-click deletes and opens a
  closed polygon;
- a `pytanga.viz.labelme` submodule that loads/stores labelme JSON in
  dataclasses and adds shapes to a scene as constant or active entities;
- the example moved to `py/examples/apps/image_labeling_app.py`, now a
  `VisualizerApp` with a File menu and CLI-driven load/save.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`) for the subsystem(s) this work touches, so the new
> code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.  The new point styles, act
> composites, and the app reuse the *existing* extension recipes (style dataclass
> + renderer + `factory.js` dispatch; `_ActWithHandles` composite; `VisualizerApp`
> + `MenuView` + `FileChooserDialog`), so no architecture change is expected.

## Architecture (short)

- **New point styles** follow the `SquarePointStyle` recipe exactly: a `PointStyle`
  dataclass in `py/pytanga/viz/_styles/_operator_styles.py`, a renderer in
  `templates/renderers/*.js`, a `style_type` dispatch branch in
  `templates/renderers/factory.js`, and re-export from `pytanga.viz`.
- **New act composites** (`ActCircle`, `ActLine`) live in `_active.py` and reuse
  `_ActWithHandles` (visual-only body + `ActPoint` handles; `remove()` tears down
  body + handles).  `ActCircle` wraps the existing `Circle` entity
  (`py/pytanga/geometry/entities/circle.py`, rendered by `circle.js` with
  `CircleStyle`); `ActLine` wraps a single `Line` segment (`Line.from_points`);
  `ActPolygon` is an open/closed `PointPath` polyline (starts open, closable).
- **Per-role handle styles**: composites gain `translate_handle_style` /
  `rotate_handle_style` so vertices/corners/radii render as circle markers and
  translate/rotate render as icon markers (material glyphs).
- **labelme module** (`py/pytanga/viz/labelme.py`) is pure data mapping — no
  transport/rendering — with dataclasses + `load`/`save`/`dumps` and an
  `add_shapes(handle, doc, *, active=…)` that maps shape types to entities/composites.
- **App** is a `VisualizerApp` subclass using the existing `MenuView` /
  `FileChooserDialog` seam (see `py/examples/viz/ui/menus/file_open_menu.py`).

## Fixed contract (up front)

### Point styles

```python
@dataclass
class CirclePointStyle(PointStyle):
    thickness: float | None = None      # slab depth along +z (like SquarePointStyle)
    filled: bool | None = None          # True = filled disc, False = outline ring
    fill_opacity: float | None = None   # fill opacity when filled (defaults to opacity)
    # to_dict() -> {"style_type": "CirclePointStyle", ...non-None fields...}
    # "size" (inherited) is the circle's radius in world units.

@dataclass
class IconPointStyle(PointStyle):
    icon: Icon | None = None            # "material:open_with" etc. (any material:* glyph)
    # to_dict() -> {"style_type": "IconPointStyle", "icon": ..., ...}
    # "size" (inherited) is the glyph's half-extent in world units.
```

### Composites (new/changed params)

```python
ActRectangle2D(center=None, size=None, *, angle=0.0, min_size=None,
               show_translate_handle=True, show_rotate_handle=True,
               handle_style: PointStyle | None = None,
               translate_handle_style: PointStyle | None = None,
               rotate_handle_style: PointStyle | None = None,
               on_corner_drag=None, on_translate=None, on_rotate=None,
               on_change=None, on_click=None)

ActEllipse(..., min_radius: float | None = None,
           translate_handle_style=None, rotate_handle_style=None, ...)

ActCircle(center=None, radius=1.0, *, min_radius=None,
          show_translate_handle=True,
          handle_style=None, translate_handle_style=None,
          on_radius_drag=None, on_translate=None, on_change=None, on_click=None)

ActLine(start=None, end=None, *, show_translate_handle=True,
        handle_style=None, translate_handle_style=None,
        on_endpoint_drag=None, on_translate=None, on_change=None, on_click=None)
# ActLine wraps a single Line entity (Line.from_points(start, end)); a line has
# exactly two endpoints and is never closed.
```

- `handle_style` broadens from `SquarePointStyle | None` to `PointStyle | None`
  (any variant).  Default handle style for the composites becomes `CirclePointStyle`
  (vertices/corners/radii); translate default `IconPointStyle(icon="material:open_with")`,
  rotate default `IconPointStyle(icon="material:rotate_right")`.
- `ActRectangle2D` stores `angle` and passes it to `Rectangle2D(angle=…)`;
  `_corners()`/`_resize_corner()` become rotation-aware (project the dragged
  corner onto the rotated local axes); `_translate_by` preserves `angle`.
- `min_size` clamps `Rectangle2D` width/height during corner resize; `min_radius`
  clamps circle/ellipse radii (replacing the hard-coded `0.05`).
- `ActCircle.entity` returns a `Circle(center, radius, normal=Direction(0,0,1))`
  (the existing geometry entity), not an `Ellipse`.
- `ActLine.entity` returns a `Line` (`Line.from_points(start, end)`), and
  `ActPolygon` starts **open** (`closed=False` for the polygon tool); the user
  closes it via `auto_close` (fusing the endpoints).
- Every composite implements `create_from_points(a, b, **kwargs)` per the
  `ShapeFromPoints` protocol (two anchor points → a new composite); a generic
  `DragPreview` accepts any such factory and drives the transient-entity
  lifecycle (begin/update/finalize/discard).

### ActPolygon vertex editing (generalized)

- `_insert_endpoint(index, pos)` is generalized to `_insert_after(index, pos)`:
  inserts a vertex **after** `index` for any index (not just the end).
- `_dispatch_vertex_drag`: Ctrl+drag on **any** vertex inserts after it (one new
  vertex per drag); plain drag still moves the vertex.
- `_make_delete_bindings`: returns a Ctrl+right-click binding (plain delete) and
  a Ctrl+Shift+right-click binding (delete + open) for **every** vertex.
  `_delete_vertex(index, *, open=False)`: if only one vertex would remain, removes
  the whole composite; otherwise pops the vertex, keeps the polygon closed while
  ≥3 vertices remain, and opens it when `open` is set.

### labelme module

```python
@dataclass
class LabelShape:
    label: str
    points: list[tuple[float, float]]      # labelme image coords (y-down pixels)
    shape_type: str                        # rectangle|circle|ellipse|polygon|line|linestrip|point
    group_id: int | None = None
    description: str = ""
    flags: dict[str, Any] = field(default_factory=dict)

@dataclass
class LabelMeDocument:
    shapes: list[LabelShape]
    image_path: str = ""
    image_height: int | None = None
    image_width: int | None = None
    image_data: str | None = None          # always None (pixels are not embedded)
    version: str = "5.0.1"
    flags: dict[str, Any] = field(default_factory=dict)

class LabelMeStore:
    def __init__(self, *, allow_extensions: bool = True) -> None: ...
    def load(self, path: str | os.PathLike) -> LabelMeDocument: ...
    def loads(self, text: str) -> LabelMeDocument: ...
    def save(self, doc: LabelMeDocument, path: str | os.PathLike) -> None: ...
    def dumps(self, doc: LabelMeDocument) -> str: ...
    def add_shapes(self, handle: VizSceneHandle, doc: LabelMeDocument,
                   *, active: bool = True) -> list[object]: ...
```

Shape-type mapping (both directions):

| shape_type | entity (`active=False`) | active (`active=True`) | points encoding |
|---|---|---|---|
| `rectangle` | `Rectangle2D` | `ActRectangle2D` | 2 opposite corners → `Rectangle2D.between` |
| `circle` | `Circle` | `ActCircle` | `[center, rim]` → radius = distance |
| `ellipse` *(ext.)* | `Ellipse` | `ActEllipse` | `[center, rim_u, rim_v]` → radii + angle |
| `polygon` | `PointPath` (closed) | `ActPolygon` (closed) | vertex list (closed loop) |
| `linestrip` | `PointPath` (open) | `ActPolygon` (open) | vertex list (open) |
| `line` | `Line` | `ActLine` | 2 points |
| `point` | `Point` | `ActPoint` | 1 point |

- labelme `polygon` is **closed** by definition; open polylines map to `linestrip`
  (and 2-point open paths to `line`).
- `allow_extensions=True` round-trips the non-standard `ellipse` type; `False`
  maps an ellipse back to `circle` when `radius_u ≈ radius_v`, else to a sampled
  `polygon` (approx. 32 points), and never emits `ellipse`.

## Decisions (confirmed)

- Dedicated `ActCircle` and `ActLine` classes (not `ActEllipse` reuse).
- `ActCircle` wraps the existing `Circle` entity (`center`, `radius`,
  `normal=+z`), center translate handle + one radius handle, no rotate handle (a
  circle is rotationally symmetric).  `min_radius` clamps the radius.
- `ActLine` wraps a single `Line` entity (`Line.from_points`), two endpoint
  handles + a translate handle, no vertex insert/delete.
- `ActPolygon` starts **open** (`closed=False`) and is closable via `auto_close`;
  labelme maps open → `linestrip`, closed → `polygon`.
- Shape creation is expressed as `create_from_points(a, b)` classmethods on each
  composite, unified by a `ShapeFromPoints` protocol; a generic `DragPreview`
  drives the transient-entity lifecycle for any factory implementing it.
- Polygon creation becomes click-drag (anchor + dragged second vertex), matching
  rectangle/ellipse; this is an example/app concern, not an `ActPolygon` change.
- Ctrl+drag inserts **after** the dragged vertex (no direction logic).
- Vertex deletion: Ctrl+right-click deletes and preserves open/closed (a closed
  polygon stays closed while ≥3 vertices remain); Ctrl+Shift+right-click deletes
  and opens a closed polygon.
- Icon handles render any `material:*` glyph, defaulting to
  `material:open_with` (translate) and `material:rotate_right` (rotate).
- labelme module supports all shape types; `ellipse` is a store-extension gated
  by `allow_extensions` (default `True`).
- Example is **moved** to `py/examples/apps/image_labeling_app.py` (base of the
  app); file loading is exposed via a File menu **and** a CLI path argument.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-point-styles.md](./01-point-styles.md) | `CirclePointStyle` + `IconPointStyle` (dataclass, renderer, dispatch, export) |
| 2 | [02-handle-style-plumbing.md](./02-handle-style-plumbing.md) | per-role handle styles; composites switch to circle/icon handles |
| 3 | [03-act-rectangle2d-rotation.md](./03-act-rectangle2d-rotation.md) | `angle` + rotate handle + rotation-aware resize + `min_size` + `create_from_points` |
| 4 | [04-act-circle.md](./04-act-circle.md) | `ActCircle` (center + radius, `min_radius`) + `create_from_points`; `ActEllipse.min_radius` |
| 5 | [05-act-polygon-vertex-editing.md](./05-act-polygon-vertex-editing.md) | insert-after-any-vertex + delete-any-vertex + `create_from_points` (open) |
| 6 | [06-act-line.md](./06-act-line.md) | `ActLine` single-`Line` composite + `create_from_points` |
| 7 | [07-draw-preview.md](./07-draw-preview.md) | `ShapeFromPoints` protocol + `DragPreview` |
| 8 | [08-labelme-module.md](./08-labelme-module.md) | `pytanga.viz.labelme` dataclasses + load/save + `add_shapes` |
| 9 | [09-example-app.md](./09-example-app.md) | move example to `py/examples/apps/`; click-drag polygon; File menu + CLI |
| 10 | [10-docs-changelog.md](./10-docs-changelog.md) | docs, dev-docs, changelog, example-doc regeneration |

## Testing as you go

- Python (each backend phase): `uv run pytest py/tests/viz -q`
- Frontend (phases 1–2): `node --check` on the new renderers +
  `uv run python tools/build-viewer-js.py --check`
- Full backend (final): `uv run pytest -q` · `uv run ruff check .` · `uv run ty check`
- JS gate (final): `node --test 'js/dev/tests/*.test.mjs'` +
  `node js/dev/tests/check-syntax.mjs`
- Example docs (phase 10): `uv run python tools/generate-example-docs.py --check`
- Docs (phase 10): `uv run mkdocs build --strict`

## Non-goals

- No new geometry MV-backed entities — `ActCircle` wraps the existing `Circle`,
  `ActLine` wraps the existing `Line` (both viz-only).
- No labelme `imageData` pixel embedding (only `imagePath` + `imageHeight/Width`).
- No undo/redo for shape edits.
- No palette/class-list management, no COCO/other export formats.
- No polygon edge-vertex snapping or auto-close tuning beyond the existing
  `close_tolerance`.



