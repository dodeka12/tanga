# Plane Drag Surface — Overview

**Created:** 2026-09-29 | **Status:** Done | **Branch:** `feat/plane-drag-surface`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Generalize the drag-to-draw interaction surface so it works on **any plane
defined by a `CoordinateMapper`** — not just the flat `z = 0` `ImageCanvas`
pixel plane — and wire it into the calibrated labeling example. This is "Level
1" of the plane-surface work: the plane is always **perpendicular to the camera's
optical axis** (the `CalibratedPlaneMapper` plane), which the existing
`DragMode.VIEW_PLANE` already handles with **no frontend change**. A fully
arbitrary plane (`DragMode.PLANE`) is explicitly out of scope (Level 2).

## Architecture (short)

- `CoordinateMapper` (in `pytanga.viz.camera`) already abstracts pixel↔world. We
  add a `plane() -> (Point, Direction)` accessor so a drag surface can recover
  the geometric plane (`PlanarMapper` → `z = 0`; `CalibratedPlaneMapper` → plane
  ⟂ optical axis at `depth`).
- `ActImagePlane` (`pytanga.viz._active`) is the only flat-2D-specific piece: its
  `interaction_config` emits `DragMode.XY_PLANE` and its `drag_anchor` hardcodes
  the ray↔`z = 0` intersection.  It becomes mapper-aware: `drag_anchor` does a
  generic ray↔plane intersection via `mapper.plane()`, and `interaction_config`
  uses `DragMode.VIEW_PLANE`.
- The rendered entity is decoupled: the flat `ImageCanvas` keeps its `ImageView`
  as the raycast target; the calibrated case uses a transparent raycastable
  plane at the annotation depth (the `CameraView.background_image` is the visual,
  not the hit target).
- `ImageCanvas` keeps its current flat behavior unchanged (it simply supplies the
  default `PlanarMapper`); the calibrated labeling example
  (`py/examples/apps/calibrated_labeling_app.py`) gains drag-to-draw on the
  calibrated pane.

## Decisions (confirmed)

- **`plane()` accessor on `CoordinateMapper`** — returns `(point_on_plane,
  normal)` in world space. `PlanarMapper` → `(Point(0,0,0), Direction(0,0,1))`;
  `CalibratedPlaneMapper` → the principal point at `depth` plus the optical-axis
  direction.
- **`ActImagePlane` gains `mapper: CoordinateMapper | None = None`** (default
  `PlanarMapper()`), and its `drag_anchor` becomes a generic ray↔plane
  intersection (no more `z = 0` hardcode).
- **`drag_mode` switches `XY_PLANE` → `VIEW_PLANE`.** `VIEW_PLANE` is "plane ⟂
  camera view at the anchor depth" — identical to `XY_PLANE` for the flat 2D
  top-down camera and correct for a calibrated pinhole camera, so one mode covers
  both. A flat-`ImageCanvas` regression test guards this.
- **Entity decoupling** — `ActImagePlane` no longer requires an `ImageView`; the
  flat case passes one, the calibrated case passes a transparent raycastable
  plane (a `Plane` geometry entity) as the hit target.
- **`ImageCanvas` is unchanged** — it supplies the default `PlanarMapper` and its
  `ImageView`, so the image-labeling app behavior is preserved.

## Contract (fixed)

```python
# py/pytanga/viz/camera.py — CoordinateMapper protocol gains:
def plane(self) -> tuple[Point, Direction]:
    """Return (point_on_plane, unit_normal) in world coordinates."""

class PlanarMapper:
    def plane(self) -> tuple[Point, Direction]:
        return Point(0.0, 0.0, 0.0), Direction(0.0, 0.0, 1.0)

class CalibratedPlaneMapper:
    def plane(self) -> tuple[Point, Direction]:
        # principal point at `depth` on the optical axis; normal = optical axis.
        point = self.to_world(self._cx, self._cy)
        center = self._camera.camera_center()
        normal = Direction(
            point.x - center[0], point.y - center[1], point.z - center[2]
        ).normalized()
        return point, normal
```

```python
# py/pytanga/viz/_active.py — ActImagePlane:
def __init__(
    self,
    image_view: ImageView | None = None,   # flat case: rendered image plane
    *,
    mapper: CoordinateMapper | None = None,  # default PlanarMapper()
    entity: Any | None = None,             # calibrated case: transparent hit plane
    handler=..., on_drag_start=..., ...,
) -> None: ...

def drag_anchor(self, ray_origin, ray_direction) -> Point:
    point, normal = self._mapper.plane()
    # generic ray ↔ plane intersection
    ...

@property
def interaction_config(self) -> InteractionConfig:
    # ... same triggers, but drag_mode=DragMode.VIEW_PLANE
```

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-coordinate-mapper-plane.md](./01-coordinate-mapper-plane.md) | `CoordinateMapper.plane()` + tests |
| 2 | [02-act-plane-mapper.md](./02-act-plane-mapper.md) | Generalize `ActImagePlane` (mapper, drag_anchor, VIEW_PLANE, entity) |
| 3 | [03-calibrated-drag-draw.md](./03-calibrated-drag-draw.md) | Drag-to-draw in the calibrated labeling example |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Docs + changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q` (targeted per phase)
- `uv run ruff check .`
- `uv run ty check`
- `uv run python tools/generate-example-docs.py --check` (phase 3)
- `uv run mkdocs build --strict` (phase 4)

## Non-goals

- No arbitrary-plane drag mode (`DragMode.PLANE`) — Level 2, out of scope.
- No frontend (`js/`) changes.
- No change to `ImageCanvas`'s flat behavior or the image-labeling app.
- No change to `DragPreview`, the `Act*` shape classes, or the toolbar (they are
  already coordinate-system-agnostic).
