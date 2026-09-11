# Viz Ideal Drag Anchor — Overview

**Created:** 2026-08-31 | **Status:** Done | **Branch:** `fix/scene-alert`

## Goal

1. Make interactive objects drag from an **ideal anchor** — a point on the
   object's ideal geometry — instead of the raw ray/mesh hit point. Today the
   frontend anchors the drag at `hit.intersect.point` (the surface of the
   rendered mesh), so an `ActPoint` (a sphere of radius = point size) picks up
   the sphere's surface offset along the constraint-plane normal. With
   `ActPoint(Point(0, 2, 0), drag_mode=DragMode.XY_PLANE)` viewed down the
   z-axis this shows up as a spurious z-component that grows with every grab
   (default hover-scale 1.5 → effective radius ≈ 0.225 per grab).
2. Introduce a per-type `ActSceneObject.drag_anchor(ray_origin, ray_direction)
   -> Point` hook. `ActPoint` returns its centre; a future `ActCircle` (drawn as
   a torus) would return the nearest point on the ideal circle, so the torus
   radius never leaks into the drag.

## Architecture (short)

- The backend owns the ideal geometry (`pytanga.geometry`); the frontend only
  does picking (raycast against meshes). The frontend sends the world-space
  picking ray with `drag_start`; the backend computes the ideal anchor and
  replies with a targeted `interaction:drag_anchor` message; the frontend
  rebases its drag accumulation onto that anchor.
- The constraint plane (`drag_mode`) stays on the frontend and is applied to the
  per-frame deltas after anchoring: pixel deltas are buffered while the anchor
  is pending and converted to world space once, at the anchor's depth (the
  existing `_axisMappedDelta` / `_projectToPlane` math is unchanged, just
  deferred).

## Decisions (confirmed)

- **Wire contract (fixed).**
  - Frontend `drag_start` gains `ray_origin: [x, y, z]` and
    `ray_direction: [x, y, z]` (world space, from `raycaster.ray`, captured at
    **pointerdown** — not on the first move, because the raycaster is reused for
    hover on `pointermove`).
  - Backend replies, to the originating browser only:
    `{ "type": "interaction:drag_anchor", "object_id": "<id>",
    "world_position": [ax, ay, az] }`.
- **`drag_anchor` semantics.** `ActSceneObject.drag_anchor(ray_origin: Point,
  ray_direction: Direction) -> Point`; the base raises `NotImplementedError`;
  `ActPoint.drag_anchor` returns `self._point` (ignores the ray). The ideal
  point of a `Point` has no extent, so the grab "snaps" to the centre; the old
  ≤radius mesh-surface grab offset is intentionally dropped.
- **The ray is the input** (not the hit point), because "nearest point on the
  ideal geometry to the ray" is the correct definition for positive-dimensional
  ideals (circle/line/sphere); `ActPoint` simply ignores it.
- **Anchor computation lives in the visualizer**, not in the per-object handler
  registry, so it never collides with a user-supplied `on_drag_start` handler.
  `Visualizer._dispatch_interaction_event` intercepts `DRAG_START`, computes the
  anchor, and sends it; a `NotImplementedError` from an unconfigured subclass
  silently skips the anchor (today's behaviour preserved).
- **Pixel deltas are buffered, not world deltas.** While the anchor is pending
  the frontend accumulates raw screen-pixel deltas (`dx`/`dy`) and converts them
  to world space exactly once, in `setDragAnchor`, using the screen-plane vectors
  recomputed at the anchor (`_computeScreenPlaneVectors(anchor)`).  This
  re-anchors both the position and the pixel→world scale onto the ideal
  geometry, so future positive-dimensional actives (circle/sphere) drag at the
  correct speed with no per-class work.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-drag-anchor-python.md](./01-drag-anchor-python.md) | `drag_anchor` hook, ray fields, backend anchor reply |
| 2 | [02-drag-anchor-frontend.md](./02-drag-anchor-frontend.md) | Send the ray, handle `drag_anchor`, rebase accumulation |
| 3 | [03-tests.md](./03-tests.md) | Unit tests for the hook, parsing, coalescing, dispatch |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Docs + branch changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q` (every Python phase)
- `uv run ruff check py/pytanga/viz/ py/tests/viz/`
- `node --check py/pytanga/viz/templates/interaction.js &&
  node --check py/pytanga/viz/templates/views/three-view.js` (phase 2)
- `uv run mkdocs build --strict` (phase 4)

## Non-goals

- No new `ActCircle`/`ActLine`/`ActSphere` classes — the hook makes them
  trivial follow-ups; only `ActPoint` is implemented now.
- No change to the per-frame constraint math (`_axisMappedDelta` /
  `_projectToPlane`) or to click/scroll/drag_move/drag_end payloads.
- No broadcast of the anchor to other browsers (targeted to the originating
  browser only).
