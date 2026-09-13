# Interactive Rectangles — Overview

**Created:** 2026-09-13 | **Status:** In progress | **Branch:** `feat/image-view`

## Goal

Add interactive rectangles to the Tanga viewer: a `Rectangle2D` entity (a flat,
axis-aligned quad in the xy-plane, drawn as an outline by default with an
optional semi-transparent fill) plus an `ActRectangle2D` interactive object with
square corner handles for resizing and an optional translation handle.  Both are
general classes usable in any 2D scene (`space_dim == 2`) and render on the
xy-plane in a 3D scene.  `ImageCanvas` gains a `draw_rectangle()` convenience
that lets the user drag out the initial rectangle and then wraps it in an
`ActRectangle2D`.

## Architecture (short)

- **Entity** — `Rectangle2D` (frozen dataclass in `pytanga.geometry.entities`):
  `center`, `size=(w,h)`, `normal=+z`, `angle=0` (axis-aligned for now).
  Rendered by a new `rectangle2d.js` renderer (outline by default, fill opt-in).
- **Style** — `Rectangle2DStyle` (color/opacity/fill/fill_opacity/thickness);
  `SquarePointStyle` (a `PointStyle` variant) so `ActPoint` handles render as
  small square markers.
- **Interactive object** — `ActRectangle2D(ActSceneObject)`: the body is a
  non-interactive `Rectangle2D`; its `_init` spawns child `ActPoint` handles
  (4 corners + 1 optional translation handle).  Default behaviour: corner drag
  resizes (opposite corner fixed), translation handle moves the whole rectangle.
  Handlers are overridable (same contract as `ActPoint`), plus an `on_change`
  notification.
- **Draw flow** — `ImageCanvas.draw_rectangle(on_done=...)` runs an initial
  drag binding that previews the rectangle and, on drag end, removes the preview
  and constructs the `ActRectangle2D`.

## Canonical wire contract (fixed up front)

### `Rectangle2D` entity (JSON, in the scene object list)

```json
{
  "kind": "Rectangle2D",
  "center": [x, y, z],
  "size": [w, h],
  "normal": [0, 0, 1],
  "angle": 0.0,
  "style": {
    "style_type": "Rectangle2DStyle",
    "color": "#ffffff",
    "opacity": 1.0,
    "fill": false,
    "fill_opacity": null,
    "thickness": 2
  }
}
```

- `size` is the full width (x) and height (y); `center` is the midpoint.
- `normal` defaults to `+z` (xy-plane); `angle` is the in-plane rotation in
  radians, `0.0` = axis-aligned (the only value `ActRectangle2D` produces for now).

### `SquarePointStyle` (JSON, as a `Point` entity's `style`)

```json
{ "style_type": "SquarePointStyle", "color": "#ffffff", "size": 6, "thickness": 1 }
```

- `size` is the half-extent of the square marker (world units); `thickness` the
  slab depth (≈0 for a flat marker).  Dispatched in `factory.js` by
  `ent.style?.style_type === 'SquarePointStyle'`, exactly like
  `CrossHairPointStyle`.

## Decisions (confirmed)

- Rectangle is **outline-only by default**; a semi-transparent fill is opt-in via
  `Rectangle2DStyle(fill=True, fill_opacity=...)`.
- **Axis-aligned only** for now (`angle` stays `0`; no rotation handle in v1 —
  rotation is a follow-up).
- `Rectangle2D` and `ActRectangle2D` are **general classes**: any 2D scene
  (`space_dim == 2`), and rendered on the xy-plane in 3D.
- `ActPoint` gains a `SquarePointStyle` (square marker) for handles; handles are
  `ActPoint` instances reusing the existing `set_interaction`/`on_interaction`
  machinery.
- `ActRectangle2D` is a **composite**: the body has no interaction of its own;
  all interaction is via child handle entities (the frontend raycasts one mesh
  per entity, so separate grabbable parts must be separate entities).
- Changelog is appended to the branch changelog
  `docs/changelog/2026/09/13_feat-image-view.md` (see `dev/workflows/changelog.md`).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-act-point-square-style.md](./01-act-point-square-style.md) | `SquarePointStyle` + square point renderer (square handle marker) |
| 2 | [02-rectangle2d-entity.md](./02-rectangle2d-entity.md) | `Rectangle2D` entity + `Rectangle2DStyle` + serializer |
| 3 | [03-rectangle2d-renderer.md](./03-rectangle2d-renderer.md) | `rectangle2d.js` renderer (outline + optional fill) + factory wiring |
| 4 | [04-act-rectangle2d.md](./04-act-rectangle2d.md) | `ActRectangle2D` (corner/translation handles, default + overridable behaviour) |
| 5 | [05-image-canvas-draw.md](./05-image-canvas-draw.md) | `ImageCanvas.draw_rectangle()` drag-to-create flow + example |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Architecture + public docs + changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz -q` (targeted files per phase) and
  `uv run pytest py/tests/geometry -q` for the entity.
- **JS (pure):** `node --check py/pytanga/viz/templates/renderers/rectangle2d.js`.
- **Bundle:** `uv run python tools/build-viewer-js.py` after any template edit
  (drift gate in pre-commit).
- **Lint/type:** `uv run ruff check ... && uv run ruff format --check ...` and
  `uv run ty check`.
- **Docs:** `uv run mkdocs build --strict`.

## Non-goals

- No rotation handle / arbitrary-angle rectangles (deferred).
- No new `DragMode` — handles reuse `XY_PLANE`.
- No SDF mapping for `Rectangle2D`.
- No change to the `ActSceneObject` 1-entity contract; `ActRectangle2D` composes
  existing `ActPoint` handles rather than adding a multi-hit entity model.

## Deferred (follow-up)

- Rotation handle + `angle` != 0 (corner resize on a rotated rectangle needs
  extra math).
- Per-corner / per-handle hover+click customisation beyond `ActPointStyle`.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
