# Viz Canonical Frame + Transform Placement — Overview

**Created:** 2026-09-21 | **Status:** Done | **Branch:** `feat/viz-canonical-frame-transform`

## Goal

Make every scene entity render in a **canonical frame** (origin-anchored,
axis-aligned, three.js-default orientation) and handle **all** placement and
rotation through a single per-entity `Transform` (quaternion TRS) applied via
the per-entity `THREE.Group` that already exists (`wrapWithNodeTransform`).
This removes the double-placement system (baked `center`/`normal`/… in each
renderer **plus** the node transform) and fixes the root cause of the
`Circle`-center update bug — and the broader per-kind update-parity gap —
instead of patching symptoms.

## Architecture (short)

- `Transform` and the pure transform math move into `pytanga.geometry`
  (`geometry/transform.py` class + `geometry/transforms.py` math); `viz` keeps
  thin re-export shims. `Transform` stores a **quaternion** for rotation (single
  source of truth); `matrix()` is computed lazily; `to_dict()` emits
  `rotation: [x, y, z, w]`.
- The scene graph (`VizSceneObject.transform`) is initialized from the entity's
  placement via a new `_entity_decompose(entity) -> (Transform, shape)`.
- The serializer emits **shape-only** content (no `center`/`normal`/`axis`/
  `origin`/`direction`/`vertex`/`rotation`/`startDirection`); placement rides on
  the node `transform` (which `serialize()` already emits).
- Frontend renderers draw canonical shapes; `applyTransformToObject`
  (`scene-builder.js`) applies the quaternion TRS to the wrapping group.
- Placement changes flow through the existing `transform` aspect; shape changes
  through `content`; `set_entity` diffs the two with a configurable epsilon.

## Canonical contract (fixed up front)

Every entity decomposes into `(Transform, shape)`:

- **Linear primitives** (`Line`, `Cylinder`, `Cone`, `Direction`, `Parabola`,
  `Hyperbola` along an axis): canonical axis **+Y** (three.js
  `CylinderGeometry`/`ConeGeometry` default), origin at the node position.
- **Planar primitives** (`Circle`, `Arc`, `Disk`, `PartialDisk`, `Ellipse`,
  `RegularPolygon`, `Rectangle2D`, `Plane`, `PlanePair`): canonical plane
  **XY** (normal +Z), centered at the node position.
- **Volumes** (`Sphere`, `Box`, `Ellipsoid`): centered at the node position,
  axis-aligned (Box/Ellipsoid `rotation` → quaternion).
- `Point`/`HPoint`: `position` = the point, identity rotation.

`_entity_decompose` maps:

- `center` / `origin` / `vertex` / `point` → `position`.
- `normal` / `axis` / `direction` (+ `startDirection`/`dirU`/`dirV`/horizontal
  axis where a second axis is needed) → quaternion.
- `rotation` (Box/Ellipsoid) → quaternion (already Euler → convert).
- everything else → shape params.

`Transform` operator overloading (applies to `Point` and `Direction`):

- `transform @ Point(...)` → transformed `Point` (T·R·S).
- `transform @ Direction(...)` → transformed `Direction` (R·S, no translation).
- `point @ transform` / `direction @ transform` → same (via `__rmatmul__`).
- `apply(obj)` is the shared helper; `__mul__`/`__rmul__` mirror `@`.

## Decisions (confirmed)

- Placement → transform derivation lives in **Python** (serializer/node), not
  the frontend.
- `Transform` stores a **quaternion** internally and emits it on the wire
  (`rotation: [x, y, z, w]`); no second Euler copy.
- `set_entity` diffs shape vs placement with a **configurable epsilon**
  (default `1e-9`) so float noise doesn't recreate meshes.
- Canonical axes are three.js defaults: **+Y** linear, **XY/+Z** planar.
- GA operators, `Axis`/`Axes*`/`Grid`/`Space`, SDF/ray/image, and
  `PointPath`/`Curve`/`PointSet` are **left as-is** (rebuild on param change).
- `Frustum` is re-parameterized (origin/axis/near/far/half-width/half-height/
  horizontal-axis) so it participates in the transform placement + diffing.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-transform-module.md](./01-transform-module.md) | Move `Transform` + transform math into `pytanga.geometry` (behavior-identical; viz shims). |
| 2 | [02-transform-quaternion.md](./02-transform-quaternion.md) | Quaternion storage + wire; `Point`/`Direction` operator overloads; frontend apply. |
| 3 | [03-entity-decompose.md](./03-entity-decompose.md) | `_entity_decompose` + node transform init + `set_entity` diffing (epsilon). |
| 4 | [04-serializer-canonical.md](./04-serializer-canonical.md) | Shape-only serialization; glTF exporter reads node transform. |
| 5 | [05-canonical-renderers.md](./05-canonical-renderers.md) | Renderers draw canonical shapes; simplify `update<Kind>()`. |
| 6 | [06-frustum-parameterize.md](./06-frustum-parameterize.md) | Re-parameterize `Frustum` (class + serializer + renderer + `from_camera`). |
| 7 | [07-bundle-tests.md](./07-bundle-tests.md) | Rebuild `js/tanga-viewer.js` + full validation. |
| 8 | [08-docs-changelog.md](./08-docs-changelog.md) | Architecture docs + changelog. |

## Testing as you go

- `uv run pytest py/tests/viz -q` and `uv run pytest -q` — Python (each phase).
- `node --check py/pytanga/viz/templates/renderers/<file>.js` — JS syntax.
- `uv run python tools/build-viewer-js.py --check` — bundle in sync (Phase 7).
- `uv run mkdocs build --strict` — docs (Phase 8).

## Non-goals

- GA operators, `Axis`/`Axes2D`/`Axes3D`/`Grid`/`Space`, SDF/ray/image — rebuild
  on param change, unchanged.
- `PointPath`/`Curve`/`PointSet` — points are the shape; no placement.
- A JS unit-test harness (JS gated by `node --check` + bundle `--check` + pytest).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
