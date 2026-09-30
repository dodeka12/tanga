# Changes since version 2.12.1

## New Features

- **Per-pane `InteractionSurface`** — a reusable interaction primitive: a
  `SceneView` pane plus a `CoordinateMapper` (which defines a plane via
  `plane()`) plus pane-level `on_drag_start`/`on_drag`/`on_drag_end`/`on_click`
  handlers, with **no scene entity**.  The frontend emits drag/click events for
  the pane's empty space by intersecting the mouse ray with the serialized
  `{point, normal}`, and the backend resolves world positions on the plane.
  `SceneView(surface=…)` binds it; `SceneView(read_only=True)` suppresses
  surface + `Act*` interaction on a pane while navigation keeps working.
- **`CalibratedSurface`** — an `InteractionSurface` on the ⟂-optical-axis plane
  at a fixed `depth` (`CalibratedPlaneMapper`).

## Breaking Changes

- **`ImageCanvas.act_plane` → `ImageCanvas.surface`** — the flat image canvas is
  refactored onto an `InteractionSurface`; the `ImageView` is now visual-only
  (no longer raycastable), and the interactive surface is `ImageCanvas.surface`.

## Bug Fixes

- **Calibrated drag-to-draw** — the calibrated labeling example no longer drops
  an interactive `Plane` into the shared world scene (which broke navigation and
  was interactive in both panes).  Drag-to-draw is bound to the image pane's
  surface only, and the overview pane is read-only.
