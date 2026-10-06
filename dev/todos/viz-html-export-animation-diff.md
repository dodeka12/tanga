# Standalone HTML export — animation playback efficiency (analysis + improvement ideas)

**Created:** 2026-10-06 | **Status:** Analysis / sketch | **Branch:** `fix/viz-control-refactor`

Analysis of the standalone/animated HTML export, prompted by the impression that
an animated export does not run smoothly even when only object positions/rotations
change.  The concern: "ensure that if only positions/rotation change, the meshes
are not recreated at each step and the scene graph is kept intact — only the
transforms should change."

**Bottom line:** the playback engine already does exactly this for the *placement*
entity kinds.  It reconciles frames by entity id and mutates only the wrapper
`Object3D`'s `position`/`quaternion`/`scale` in place — no mesh recreation, no
scene-graph teardown.  A "diff" already exists at playback time.  What is *not*
done is diffing at **export** time (the HTML still stores a full snapshot per
frame), and there are a few per-frame overheads and a handful of entity kinds that
legitimately rebuild.  Details and improvement ideas below.

## Current pipeline (three stages)

1. **Capture (export time, Python).** `AnimationRecording.capture_frame()` calls
   `Scene.full_state()` and appends a **complete, id-keyed snapshot of every
   object** each frame — no diffing.
   - `py/pytanga/viz/export/_animation_recording.py:60-80` — `self._frames.append(list(entities))`.
   - `to_dict()` (`:152-165`) returns `{frames, frame_count, cameras, assets, frame_assets}`.

2. **Placement/shape split (serializer, Python).** `_entity_decompose()` splits
   each entity into a `Transform` (position + quaternion rotation + scale) and a
   *shape* dict, and `VizSceneObject.serialize()` emits them as separate fields.
   - `py/pytanga/viz/_decompose.py:127-278` (e.g. `Point` → `Transform(position=…) + {}`).
   - `py/pytanga/viz/_nodes.py:347-358` — `transform` is its own field alongside
     `kind`/`parent_id`/shape fields.

   Consequence: a moving `Point` produces consecutive frames that differ **only**
   in `transform.position`.

3. **Reconcile (playback time, JS).** `_reconcileFrame(frame)` is the id-based
   diff: create-on-first-seen / update-in-place / rebuild-on-structural-change /
   hide-on-absence.
   - `py/pytanga/viz/export/_bootstrap/_animation.py:220-336`.
   - The in-place branch (`:278-285`):
     ```js
     if (updateEntityMesh(mesh, ent, prev)) {
         mesh.userData._data = { ...prev, ...ent };
         mesh.visible = true;
         const entry = figRegistry.get(ent.id);
         if (entry && entry.obj) applyTransformToObject(entry.obj, ent.transform);
     }
     ```

   `updateEntityMesh` (`py/pytanga/viz/templates/renderers/factory.js:235-295`)
   routes to per-kind updaters; its generic path returns
   `!entityRequiresRebuild(ent, prev)`.  `entityRequiresRebuild`
   (`renderers/utils.js:344-406`) checks **only shape fields and non-cheap style
   fields — never `transform`**, so a transform-only change always takes the
   in-place branch.  `applyTransformToObject` (`scene-builder.js:21-26`) then sets
   `position`/`quaternion`/`scale` on the existing wrapper node.

   Covered by regression test
   `py/tests/viz/test_export_animation_transform.py` (asserts
   `applyTransformToObject(entry.obj, ent.transform)` is emitted for an in-place
   `Point` update).

## Why the "not smooth" impression is *not* mesh recreation

For the placement kinds (Point, HPoint, Direction, Line, Cylinder, Cone,
Parabola, Hyperbola, Circle, Sphere, Arc, Disk, PartialDisk, Ellipse,
RegularPolygon, Rectangle2D, Plane, Box, Ellipsoid, Frustum) the per-kind
updaters only rebuild on shape/style change, never on `transform`:
- `updateLine` (`renderers/line.js:56-76`) — rebuilds only on style / fat-line↔cylinder / length.
- `updateCircle` (`renderers/circle.js:90-99`) — rebuilds only on radius/tubeRadius/style.
- `updateDirection` (`renderers/direction.js:46-52`) — rebuilds only on style/length.

So the scene graph and meshes already stay intact; only transforms change.

## Remaining costs / improvement opportunities

1. **Export-time diff (file size, not playback).** `capture_frame()` stores full
   snapshots per frame, so the HTML JSON is dominated by redundant state
   (scale ~ `frames × entities`).  Gzip (`compress=True`) helps, but a real
   keyframe/delta format would shrink load time and parse/memory footprint.
   This is the natural place a "diff" is still missing.  Options:
   - Frame 0 as full state, subsequent frames as per-id deltas (only changed
     entities/fields).
   - Teach `_reconcileFrame` to expand deltas, or read them directly (keep the
     same `prev` = `mesh.userData._data` accumulation).

2. **Short-circuit transform-only frames.** Even for a pure transform change,
   `_reconcileFrame` calls `updateEntityMesh` → `applyStyleUpdate` for *every*
   entity every frame, which does `mesh.traverse()` plus repeated
   `JSON.stringify` comparisons.  Cheap relative to recreation, but O(N) per
   frame.  Detect "only `transform` differs from `prev`" and go straight to
   `applyTransformToObject(entry.obj, ent.transform)`.

3. **De-async / trim the hot loop.** `_figAnimate` is `async` and awaits
   `_playFrame` (`_animation.py:388-413`), which also runs `figControls.update()`
   + WebGL + CSS2D renders + `_updateScrubBar()` (DOM writes) every rAF.  The
   async/await microtask overhead and unconditional `controls.update()`/scrub
   DOM write could be reduced.

4. **Entity kinds that still rebuild every frame** (position baked into content,
   not a separable transform): `PointPath` (always rebuilds — `entityRequiresRebuild`
   returns true), `PointSet`/`Curve`/`PlaneConic` (rebuild when points change),
   and `Axis`/`Axes2D`/`Axes3D`/`Grid` (always rebuild).  For these a rebuild is
   inherent to the geometry, but buffer updates (`geometry.setPositions`) are
   possible for some instead of full geometry recreation.

5. **Possible camera fight (separate concern).** For exports with per-frame
   cameras (e.g. `_output/animated_camera_3d.html`), `_playFrame` calls
   `applyCameraConfig` (sets position/lookAt/target/`updateProjectionMatrix`/
   `controls.update()`), then the render loop calls `figControls.update()` again.
   Worth checking if the jitter is camera-driven rather than object-driven.
