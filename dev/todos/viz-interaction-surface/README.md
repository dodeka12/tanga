# Interaction Surface — Overview

**Created:** 2026-09-29 | **Status:** Planned | **Branch:** `feat/interaction-surface`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Introduce a general **interaction surface** — a per-pane interaction plane that
captures pointer/drag events and maps them to world positions via a
`CoordinateMapper` — and make it the single mechanism behind both the flat
`ImageCanvas` and a calibrated `CameraView.background_image`.  The `ImageLabeler`
example (and any future editor) then sits on this one surface, instead of
reaching into `ImageCanvas` internals.

This replaces the failed phase-3 "transparent `Plane` in the shared scene" hack:
interaction becomes **per-pane**, and the rendered image (visual) is a separate
concern from the interaction plane (surface).

## Architecture (short)

Three orthogonal concerns:

- **pane** — a `SceneView` (its `CameraView` supplies camera + navigation + the
  optional background image).  A pane can be `read_only` (orbit/pan only, no
  surface and no `Act`-object editing).
- **surface** — an `InteractionSurface` bound to a pane: a `CoordinateMapper`
  (which defines the plane + pixel↔world) plus pane-level
  `on_drag_start`/`on_drag`/`on_drag_end`/`on_click` handlers.
- **visual** — the image, an orthogonal rendering detail: `ImageView` (flat
  `ImageCanvas`) or `CameraView.background_image` (calibrated).

The frontend already runs one `InteractionController` per pane and already does
ray↔plane intersection for drag; the missing piece is emitting pointer events
for the **pane itself** (empty space) when a surface is present, instead of only
when an entity is raycast.

## Decisions (confirmed)

- **`InteractionSurface` = pane + `CoordinateMapper` + pointer handlers.** The
  surface resolves pointer→world via `camera.pixel_ray` + `mapper.plane()`
  (reusing the ray↔plane intersection from the `CoordinateMapper` work), so it
  needs no raycastable entity.
- **The visual is separate and optional.** `ImageCanvas` keeps its `ImageView`
  quad as the visual; the calibrated case uses `CameraView.background_image`.
- **`SceneView` gains `surface=` and `read_only=`.** `read_only` disables the
  surface and suppresses `Act`-object editing on that pane (the world pane), but
  leaves navigation (orbit/pan/zoom) working.
- **`ImageCanvas` is refactored onto the surface** (its `ActImagePlane` drag
  logic moves to the surface; the `ImageView` stays as visual). Backward
  compatibility is preserved for existing `ImageCanvas` callers.
- **A small frontend change is required** (per-pane surface pointer events), so
  a manual browser smoke test is mandatory for the surface phases.

## Contract (fixed)

```python
# py/pytanga/viz/ (new)
class InteractionSurface:
    def __init__(
        self,
        mapper: CoordinateMapper,
        *,
        on_drag_start: Callable[[Point], None] | None = None,
        on_drag: Callable[[Point], bool] | None = None,
        on_drag_end: Callable[[Point], None] | None = None,
        on_click: Callable[[Point], None] | None = None,
    ) -> None: ...
    def serialize(self) -> dict[str, Any]: ...   # {point, normal} of mapper.plane()

# py/pytanga/viz/views/scene_view.py
SceneView(scene, *, camera_view=..., surface: InteractionSurface | None = None,
          read_only: bool = False, ...)
```

- `SceneView._serialize` emits `"surface": {point, normal, id}` and
  `"read_only": true` (when set) in the `scene_view` node.
- The surface's pointer handlers are registered under the surface id in the same
  `(id, event)` registry as `Act` objects (`origin=INTERACTION`).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 0 | [00-revert-plane-hit-surface.md](./00-revert-plane-hit-surface.md) | Revert the prior `Plane` hit-surface wiring |
| 1 | [01-pane-pointer-surface.md](./01-pane-pointer-surface.md) | Per-pane pointer surface (frontend + `InteractionSurface` + `SceneView` fields) |
| 2 | [02-imagecanvas-surface.md](./02-imagecanvas-surface.md) | Refactor `ImageCanvas` onto the surface (flat backing) |
| 3 | [03-background-surface.md](./03-background-surface.md) | Calibrated `CameraView.background_image` backing |
| 4 | [04-example.md](./04-example.md) | Rebuild the calibrated labeling example on the surface |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Docs + changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q`
- `uv run ruff check .`
- `uv run ty check`
- `node --test 'js/dev/tests/*.test.mjs'` + `node js/dev/tests/check-syntax.mjs`
- `uv run mkdocs build --strict` (phase 5)
- Manual browser smoke (phases 1–4): `uv run python py/examples/apps/calibrated_labeling_app.py`

## Non-goals

- No `DragMode.PLANE` (arbitrary, non-⟂-optical-axis plane) — still out of scope.
- No change to `DragPreview`, the `Act*` shape classes, or the toolbar logic.
- No per-pane `hide`/`show` changes.
