# Animation Exports: Frame-Snapshot Reconciliation + Renderer-Owned Updates

## Problem

`AnimationRecording.__init__` snapshots `initial_state` *before* any `viz.add(...)`, so it is
always an empty list. The frames themselves — produced by `capture_frame()` calling
`Scene.full_state()` — are complete, id-keyed snapshots of every object (scene entities and
overlay labels). Because `Scene` assigns a stable UUID8 id to each object, each frame already
carries a stable `id` for reconciliation.

The JS engine currently relies on `initial_state` (`js_entity_creation(entities_expr="initial", ...)`)
to create meshes at startup, then replays frames through `applyFrameUpdate`. Since `initial_state`
is empty, animated exports start with no meshes and depend on frame replay. Playback and
scrubbing also walk frames one-by-one, making a seek O(number-of-frames).

## Root cause of the rendering bugs

The live viewer and the animated export both call the **same creation renderers**
(`createLine`, `createPointPath`, …) through `createEntityMesh`. The divergence is in the
**update** path that runs on subsequent frames:

- Live view: `viewer.js` → `inPlaceUpdate()` + `updateEntity()`.
- Animated export: `_bootstrap/_animation.py` → `applyFrameUpdate()`.

`applyFrameUpdate()` is a hand-written reimplementation of `inPlaceUpdate()` that has drifted in
two ways:

1. **Straight lines render centered on the origin.** `createLine` (`line.js`) positions the
   cylinder at the segment **midpoint** `origin + normalize(direction) * length / 2`. The live
   view's `inPlaceUpdate` has an `ent.kind === 'Line'` branch that recomputes that midpoint and
   returns `false` when `length` changes. `applyFrameUpdate` lacks that branch — it sets the mesh
   position to `origin`, moving the cylinder's center to the start point.
2. **`PointPath` is never drawn.** `createPointPath` (`point_path.js`) builds fresh fat-line
   geometry from `ent.points` every time. The live view's `inPlaceUpdate` always returns `false`
   for `PointPath` (forcing a rebuild). `applyFrameUpdate` only rebuilds on `radius`/`extent`/`kind`
   and never reads `ent.points`, so the geometry is never regenerated.

The JSON is **not** missing data — `Scene.full_state()` already emits `origin`, `direction`,
`length`, `thickness`, `color`, `opacity`, `style` (Line) and `points`, `colors`,
`line_thickness`, `opacity` (PointPath). The export's update code simply does not act on it the
same way the live view does.

## Confirmed decisions

1. **Reconciliation is id-based, per frame.** Create-on-first-seen, update-on-seen-again,
   **hide-and-cache** on absence. No dispose during playback, so a returning entity (e.g. the
   expensive `PointPath` with hundreds of points) is not recreated.
2. **`initial_state` is removed** from the JSON file format and from all Python/JS logic. Frames
   are the single source of truth.
3. **Update semantics are co-located with creation** in each renderer module, so there is a single
   source of truth and no duplicated in-place-update logic to drift.

## Non-goals / invariant: static standalone & figure HTML must keep working

- `py/pytanga/viz/export/_html.py` (`_build_static_fullpage_adapter`) and
  `py/pytanga/viz/export/_figure_html.py` (`_build_static_figure_adapter`) call
  `js_entity_creation(...)` with their own `entities` / `figEntities` arrays and use
  `js_label_creation_static`. They do **not** reference `initial_state`, `frames`, or the animated
  reconcile path.
- Therefore `js_entity_creation` (the static branch, now the only branch) and
  `js_label_creation_static` are **left unchanged**. Only the animated path is replaced.

## Architecture

Each renderer module owns **both** `createX` and `updateX`. `factory.js` exposes a shared
**`updateEntityMesh(mesh, ent, prev)`** dispatcher (mirroring its existing `createEntityMesh`).
Both the live viewer and the animated export call this dispatcher, so a new/changed entity kind is
only ever defined once.

This works because the export already bundles `factory.js` + every `*.js` renderer module
(`generate_bootstrap_js` in `_bootstrap/_html.py`, via `_strip_imports`). Any `updateX` and the
`updateEntityMesh` dispatcher are therefore automatically available to both consumers.

---

## Implementation steps

Progress:
- [x] Step 1: `renderers/utils.js` — `applyStyleUpdate` + `entityRequiresRebuild`
- [x] Step 2: `renderers/line.js` — `updateLine`
- [x] Step 3: `renderers/point_path.js` — `updatePointPath`
- [x] Step 4: `renderers/direction.js` — `updateDirection`
- [x] Step 5: `renderers/factory.js` — `updateEntityMesh` dispatcher
- [x] Step 6: `templates/viewer.js` — `inPlaceUpdate` delegation
- [x] Step 7: `_animation_recording.py` — drop `initial_state`
- [x] Step 8: `_bootstrap/_animation.py` — reconcile engine
- [x] Step 9: `_animated_figure.py` — frame-0 reify + reconcile
- [x] Step 10: `_bootstrap/_entities.py` — remove `layer_dispatch=True`
- [x] Step 11: `_bootstrap/_html.py` — `katex_css_if_needed` scans frames

Dependencies run top-to-bottom: Phase A is pure renderer work (foundation), Phase B wires the live
viewer on top of it, Phase C removes `initial_state` on the Python side, and Phase D builds the
export reconcile engine on the shared dispatcher. No later step refactors an earlier one.

### Phase A — Co-located update functions in the renderer bundle

#### Step 1: `py/pytanga/viz/templates/renderers/utils.js`

Add two kind-agnostic helpers used by the dispatcher and by per-kind updaters:

- `applyStyleUpdate(mesh, ent)` — applies opacity, color, and scale to the mesh (and its children)
  when present in `ent`. Centralizes the common style mutations so per-kind updaters don't repeat
  them.
- `entityRequiresRebuild(ent, prev)` — returns `true` when a mesh must be rebuilt rather than
  updated in place: `kind` changed, `radius`/`extent`/`length` changed beyond tolerance (1e-9), or
  `ent.kind === 'PointPath'` (geometry derives from `points`, see Step 3).

#### Step 2: `py/pytanga/viz/templates/renderers/line.js`

Add `updateLine(mesh, ent, prev)` next to `createLine`:

- Set position to the segment midpoint `origin + normalize(direction) * length / 2`
  (using `ent.length ?? prev.length ?? 20.0`) and rotation from `direction` — mirroring `createLine`.
- Call `applyStyleUpdate(mesh, ent)`.
- Return `false` when `length` or `thickness` changed beyond tolerance (cylinder geometry depends
  on both), otherwise `true`.

#### Step 3: `py/pytanga/viz/templates/renderers/point_path.js`

Add `updatePointPath(mesh, ent, prev)` that always returns `false` — the fat-line geometry is
rebuilt from `points`/`colors`, so in-place update is never correct. (This makes
`entityRequiresRebuild`'s PointPath check redundant but is kept explicit for clarity.)

#### Step 4: `py/pytanga/viz/templates/renderers/direction.js`

Add `updateDirection(mesh, ent, prev)`:

- Set position to `origin` (arrow group sits at origin) and rotation from `vector`.
- Call `applyStyleUpdate(mesh, ent)`.
- Return `false` when `length` changed beyond tolerance (shaft/head geometry depends on it),
  otherwise `true`.

Other entity modules (point, plane, circle, sphere, operators, axes, grid, …) need **no** custom
`updateX`; they fall through to the generic path in Step 5.

#### Step 5: `py/pytanga/viz/templates/renderers/factory.js`

Add a shared dispatcher `updateEntityMesh(mesh, ent, prev)` that:

1. Routes to the co-located `updateX` when one exists (`Line` → `updateLine`,
   `PointPath` → `updatePointPath`, `Direction` → `updateDirection`).
2. Otherwise applies the generic update: position (`position` → set position; `center` → set
   position; `vector`/`direction`+`origin` → set position to `origin` and orient along the vector),
   then `applyStyleUpdate(mesh, ent)`.
3. Returns `!entityRequiresRebuild(ent, prev)`.

Keep `createEntityMesh` and `removeEntityMesh` unchanged. `updateEntityMesh` is now the single
source of in-place-update truth for both the live viewer and the animated export.

### Phase B — Live viewer delegates to the shared dispatcher

#### Step 6: `py/pytanga/viz/templates/viewer.js`

- Import `updateEntityMesh` from `./renderers/factory.js` (alongside the existing
  `createEntityMesh`/`removeEntityMesh` import).
- Replace the body of `inPlaceUpdate(ent)` with a thin delegation:
  ```javascript
  const mesh = entityMeshes.get(ent.id);
  if (!mesh) return false;
  const previous = entityData.get(ent.id);
  return updateEntityMesh(mesh, ent, previous);
  ```
- Leave `updateEntity()` unchanged: it still stores `entityData`, rebuilds via `createEntityMesh`
  on `false`, and re-attaches `userData._labels`.

### Phase C — Python recording drops `initial_state`

#### Step 7: `py/pytanga/viz/export/_animation_recording.py`

- In `__init__`, remove `self._initial_state = ...` and its print statement. Keep `self._scene`,
  `self._styles_map`, `self._frames`.
- Remove `get_initial_state()`.
- Change `to_dict()` to return only `{ "frames": self._frames, "frame_count": len(self._frames) }`
  (drop the `initial` local and its debug prints).
- Update the class/module docstrings: each `capture_frame()` snapshot is a full id-keyed state.

### Phase D — Animated export reconcile engine (uses the shared dispatcher)

#### Step 8: `py/pytanga/viz/export/_bootstrap/_animation.py`

- `_GET_ANIM_DATA_JS`: fallback object → `{ frames: [], frame_count: 0 }` (drop `initial_state`).
- `js_animation_data_init`: remove `const initial = animData.initial_state || [];`.
- Add a generator `js_reconcile_frame(...)` emitting `_reconcileFrame(frame)` that reconciles the
  frame against the previous applied id-set using the **bundled** `updateEntityMesh` dispatcher
  (no bespoke `applyFrameUpdate`):
  1. Build `const targetIds = new Set((frame || []).map(e => e.id));`.
  2. For each entity in `frame`:
     - `overlay` + `label`: create via `_createLabel` if not already in the label map, then set
       `labelObj.visible = true`.
     - scene entity: if not in `figMeshMap`, `await createEntityMesh(ent)`, add to scene, store,
       and set `mesh.userData._data = ent`. Otherwise call
       `updateEntityMesh(mesh, ent, mesh.userData._data)`, and if it returns `false`, rebuild via
       `createEntityMesh({ ...prev, ...ent })`, re-attach `userData._labels`, and replace in the map.
     - Set `mesh.visible = true`.
  3. For every `[id, mesh]` in `figMeshMap` whose id is **not** in `targetIds`, set
     `mesh.visible = false` (hide-and-cache); likewise hide absent label objects.
- Add `_playFrame(n)` that runs `if (n >= 0 && n < frames.length) await _reconcileFrame(frames[n]);`.
- Replace the render loop (`js_animated_render_loop`):
  - Emit the frame-0 reify bootstrap (async IIFE) and set `currentFrame = 0`.
  - `_figAnimate` computes `targetFrame` (loop modulo) and, when `targetFrame !== currentFrame`,
    calls `await _playFrame(targetFrame)` directly — **no frame walking**.
- Rewrite `_CONTROLS_JS`:
  - `_togglePlay` restart: `await _playFrame(0)` instead of the old `currentFrame = -1` stub.
  - `_onScrub(val)`: `await _playFrame(parseInt(val, 10)); currentFrame = target;` — direct jump.
- Remove/stop generating the old bespoke `applyFrameUpdate`.

#### Step 9: `py/pytanga/viz/export/_animated_figure.py`

In `_build_animated_figure_adapter` and `_build_animated_fullpage_adapter`:

- Remove the `js_entity_creation(entities_expr="initial", ..., layer_dispatch=True)` call.
- Emit `js_reconcile_frame(...)` (Step 8) instead, plus the frame-0 reify bootstrap.
- Give **both** paths a `labelObjects` map:
  - Figure path: use `js_animated_label_function(label_map_var="labelObjects")` and
    `js_animation_data_init(fps, extra_map_vars="\nconst labelObjects = new Map();")`, and pass
    `label_objects_map_var="labelObjects"` to `js_animated_render_loop`.
- Update the docstring `Args:` references from `initial_state` to `frames`/`frame_count`.

#### Step 10: `py/pytanga/viz/export/_bootstrap/_entities.py`

- Keep `js_label_creation_static` and the static body of `js_entity_creation` unchanged (used by
  `_html.py` / `_figure_html.py`).
- Remove the now-unused `layer_dispatch` parameter and its animated branch, since the animated path
  no longer calls it (its sole caller was removed in Step 9). Update the two static callers that
  still passed `layer_dispatch=False`.

#### Step 11: `py/pytanga/viz/export/_bootstrap/_html.py`

- `katex_css_if_needed`: replace the `recording_data.get("initial_state", [])` loop with iteration
  over all frames (`for frame in recording_data.get("frames", [])`) to detect `$` in label texts.

### No change required

- `py/pytanga/viz/export/_bootstrap/_entities.py` static branch.
- Other renderer `.js` modules (point, plane, circle, sphere, operators, axes, grid) — they use the
  generic update path in Step 5.

### Slight scope addition in Step 10

Removing the ``layer_dispatch`` parameter from ``js_entity_creation`` also required deleting the
now-invalid ``layer_dispatch=False`` keyword from its two static callers
(`py/pytanga/viz/export/_html.py` and `py/pytanga/viz/export/_figure_html.py`).  Their generated
output is otherwise unchanged — the static exports still use the same ``js_entity_creation``
static branch.

---

## Summary

| # | File | Change |
|---|------|--------|
| 1 | `renderers/utils.js` | Add `applyStyleUpdate` + `entityRequiresRebuild` |
| 2 | `renderers/line.js` | Add `updateLine` (midpoint placement, length/thickness rebuild) |
| 3 | `renderers/point_path.js` | Add `updatePointPath` (always rebuild) |
| 4 | `renderers/direction.js` | Add `updateDirection` (origin placement, length rebuild) |
| 5 | `renderers/factory.js` | Add `updateEntityMesh` dispatcher |
| 6 | `templates/viewer.js` | `inPlaceUpdate` delegates to `updateEntityMesh` |
| 7 | `_animation_recording.py` | Remove `initial_state`; `to_dict()` → `{frames, frame_count}` |
| 8 | `_bootstrap/_animation.py` | `_reconcileFrame`/`_playFrame` on shared dispatcher; direct-jump; hide-and-cache; drop bespoke `applyFrameUpdate` |
| 9 | `_animated_figure.py` | Frame-0 reify + reconcile; add `labelObjects` to figure path |
| 10 | `_bootstrap/_entities.py` | Remove unused `layer_dispatch=True` branch |
| 11 | `_bootstrap/_html.py` | `katex_css_if_needed` scans frames instead of `initial_state` |

## Testing checklist

- [ ] Animated figure: entities appear at frame 0 without playing; count matches frame 0.
- [ ] Straight line spans origin→endpoint (not centered on origin) across all frames.
- [ ] `PointPath` trail renders and follows the per-frame `points` list.
- [ ] Playback: adding/removing an entity mid-animation creates/hides it (no recreate when it returns).
- [ ] Scrub back/forward (jump to arbitrary frame) reconciles correctly in O(1) frames, not O(N).
- [ ] Kind/style change under the same id triggers rebuild (radius/extent/length/kind path).
- [ ] `initial_state` absent from exported JSON; `_getAnimData` fallback no longer references it.
- [ ] Live viewer still renders identically after `viewer.js` delegates to `updateEntityMesh`.
- [ ] Static `export_html` and `export_figure` still render (static `js_entity_creation` path).
- [ ] KaTeX label CSS still injected when labels in any frame contain `$`.