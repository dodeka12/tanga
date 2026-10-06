# Phase 9 — Example app (`py/examples/apps/image_labeling_app.py`)

## Goal

Move the labeling example into `py/examples/apps/`, convert it to a
`VisualizerApp` that loads/saves labelme JSON (via a File menu **and** a CLI
path), and change polygon creation to click-drag.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`), and `dev/workflows/example-docs.md` for the header
> format.  Uses the existing `VisualizerApp` + `MenuView` + `FileChooserDialog`
> seam; no architecture change.

## Files

- New: `py/examples/apps/image_labeling_app.py` (moved from
  `py/examples/viz/image/image_labeling.py`)
- Delete: `py/examples/viz/image/image_labeling.py`
- Edit: any docs/nav referencing the old example path

## Steps

- [x] **9.1 — Move + wrap in `VisualizerApp`**
  - Move the example to `py/examples/apps/image_labeling_app.py`; subclass
    `VisualizerApp` (title, `space_dim=2`, no axes/grid).  Move the existing
    `ShapeLabeler` logic into the app class; update the docstring + `Keywords:`
    header (`labelme, labeling, image, app, ActRectangle2D, ActCircle, ActLine`).
- [x] **9.2 — Drag-to-create via `DragPreview`**
  - Wire rect/ellipse/circle/line tools through `DragPreview` (each configured
    with the composite's `create_from_points` classmethod); polygon click-drag
    produces a 2-vertex open `ActPolygon` (closable later), then exits mode
    (one-shot) — mirroring rect/ellipse drag.
- [x] **9.3 — Labelme load/save wiring**
  - Hold a `LabelMeStore`; "Open…" (`FileChooserDialog`) → `store.load(path)` →
    clear the canvas and `add_shapes(handle, doc, active=True)`; "Save"/"Save As…"
    → build a `LabelMeDocument` from the current shapes and `store.save`.
  - Track shapes as `(act, style)` and write back via the Phase 8 inverse helper.
- [x] **9.4 — File menu**
  - A `MenuView(mode="bar")` with a "File" submenu (`Open…`, `Save`, `Save As…`,
    `Exit`) at the top of the `SplitView` (see
    `py/examples/viz/ui/menus/file_open_menu.py`).
- [x] **9.5 — CLI loading**
  - Parse a positional/`--file <path>` argument in `main()`; when given, load it
    in `init()` after the layout is shown.
- [x] **9.6 — Update the toolbar tools**
  - Add circle and line tools wired to `ActCircle`/`ActLine`; polygon produces
    open polylines (closable); each tool is a `DragPreview` over its
    `create_from_points` factory.

## Validation

```
uv run pytest py/tests/viz -q
uv run python tools/generate-example-docs.py --check
```

## Notes

- Manual browser check is required (no JS harness): draw, select, delete, and
  load/save a labelme file.
