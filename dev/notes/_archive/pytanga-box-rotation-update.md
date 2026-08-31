# Bug: `Box` rotation ignored on in-place ("content") update

**Created:** 2026-08-31 | **Status:** Reported | **Branch:** `seating-plan-app`

A standalone bug description for the pytanga repo. Documents why updating a
`Box`'s `rotation` via `Visualizer.update_entity()` does not visually rotate it
in the live viewer — a rotation-only change is silently dropped.

## Metadata

- Package: `tanga-py` (import name `pytanga`), version **1.11.0**.
- Frontend: `pytanga/viz/templates/` (bundled in the wheel).
- Severity: high — `update_entity` on a `Box` with a new `rotation` has no
  visible effect, so rotation interaction cannot work.

## Summary

A `Box`'s orientation is serialized as a top-level `rotation` Euler triple and
read by `createBox` only at creation time. The in-place update path for a
"content" patch never re-applies `rotation`, and the rebuild predicate never
flags a `rotation` change. So `update_entity(box, Box(..., rotation=...))`
updates the `center` (position) but silently ignores the new `rotation`.

## Steps to reproduce

```python
import math
from pytanga.geometry import Box, Direction, Point, Rotor
from pytanga.viz import View2DConfig, Visualizer

viz = Visualizer(space_dim=2, camera=View2DConfig(xmin=-2, xmax=2, ymin=-2, ymax=2))
bid = viz.add(Box(center=Point(0, 0, 0), size=(1.6, 0.8, 0.1)))
viz.flush()
viz.update_entity(
    bid,
    Box(center=Point(0, 0, 0), size=(1.6, 0.8, 0.1),
        rotation=Rotor(math.radians(45), Direction(0, 0, 1))),
)
viz.flush()
```

Then observe the box in the browser.

### Expected

The box rotates 45° about the z-axis.

### Actual

The box does not rotate. (Position updates *do* work — moving the box takes
effect — only the rotation is dropped.)

## Root cause

- `createBox` (`templates/renderers/box.js:22-24`) applies the orientation only
  when the mesh is created:

  ```js
  if (ent.rotation) {
      mesh.rotation.set(ent.rotation[0], ent.rotation[1], ent.rotation[2]);
  }
  ```

- On a "content" patch, `_updateEntityContent`
  (`templates/views/three-view.js:610`) calls `updateEntityMesh`
  (`templates/renderers/factory.js:167`). Its generic in-place branch
  (`factory.js:192-208`) re-applies `position`/`center` (and style) but **never
  `rotation`**, then returns `!entityRequiresRebuild(ent, prev)`.

- `entityRequiresRebuild` (`templates/renderers/utils.js:309-346`) checks
  `radius`, `alignCenter`, `extent`, `length`, `tubeRadius`, `angle`,
  `span_u`/`span_v`, `arrow`, `kind`, and style — but **not `rotation`** (and
  not `size`). So it returns `false` for a rotation-only change,
  `updateEntityMesh` reports "updated in place", and no rebuild happens.

Net effect: the `rotation` field is silently ignored on update.

## Suggested fix

Either (or both):

- In `updateEntityMesh` (`factory.js`), apply rotation in place for entities
  that carry a top-level `rotation` triple:

  ```js
  if (ent.rotation) {
      mesh.rotation.set(ent.rotation[0], ent.rotation[1], ent.rotation[2]);
  }
  ```

- In `entityRequiresRebuild` (`utils.js`), treat a `rotation` change (and, for
  completeness, a `size` change — `center` is already applied in place) as
  requiring a rebuild:

  ```js
  if (ent.rotation !== undefined && prev &&
      JSON.stringify(ent.rotation) !== JSON.stringify(prev.rotation)) return true;
  if (ent.size !== undefined && prev &&
      JSON.stringify(ent.size) !== JSON.stringify(prev.size)) return true;
  ```

## Workaround

Not applied downstream — the `seating-plan-app` repo is waiting for this
upstream fix before implementing table rotation.
