# Phase 7 — Extend the example into a multi-shape labeling tool

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If this
> work introduces or changes architecture, update the developer docs.

## Goal

Turn `py/examples/viz/image/rectangle_labeling.py` into a tool that adds and
edits rectangles, ellipses, polygons, and points on an image: a toolbar to pick
the shape type, a mixed `shapes` list with a `selected` pointer, drag-to-create
for each type, click-to-select (via body `on_click`) with highlighting, and
Delete/Backspace/Escape key handling.

## Files

- Edit: `py/examples/viz/image/rectangle_labeling.py`

## Steps

- [x] **7.1 — Modes + toolbar.**
  - Replace `adding: bool` with a mode (`rect`/`ellipse`/`polygon`/`point`) and
    `self.mode`; toolbar gets one button per type (reuse `ButtonView`/`EIconMaterial`),
    toggling the active mode.
- [x] **7.2 — Mixed storage + selection.**
  - `self.shapes: list[ActSceneObject]` (rect/ellipse/polygon/point) and
    `self.selected: ActSceneObject | None`; helper to style a shape as selected
    vs normal (re-style body color/thickness).
- [x] **7.3 — Drag-to-create per type.**
  - Rectangle: `Rectangle2D.between` (existing).  Ellipse: bounding box → radii.
    Polygon: multi-click to place vertices, then close.  Point: single click
    (`ActPoint`).  Keep the existing preview/discard pattern.
- [x] **7.4 — Selection.**
  - Pass `on_click` to each `ActRectangle2D`/`ActEllipse`/`ActPolygon`/`ActPoint`
    so clicking a shape selects it; highlight the selected shape.
- [x] **7.5 — Key handling.**
  - `viz.on_key("Delete", ...)` and `"Backspace"` → remove `self.selected`
    (calling its `remove()` and dropping it from `shapes`); `"Escape"` → deselect.
- [x] **7.6 — Header.**
  - Update the module docstring (description + `Run with:` + `Keywords:`), per
    `dev/workflows/example-docs.md`.

## Validation

```
uv run python tools/generate-example-docs.py --check
uv run pytest py/tests/viz -q
```

(Manual: run `uv run python py/examples/viz/image/rectangle_labeling.py` and
exercise add/select/edit/delete for each shape type.)

## Notes

- Keep the filename `rectangle_labeling.py` (docs link to it); update its
  docstring/Keywords to reflect the broader tool.
- Selection is example state; the act objects themselves stay generic.
