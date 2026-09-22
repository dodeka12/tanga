# Phase 3 — Per-pane camera lock (`SceneView.lock`)

## Goal

Add `SceneView(lock={"rotate","pan","zoom"})` so parts of one pane's camera can
be fixed while other panes (of the same scene) stay free. Serialize the set in
the `scene_view` node and disable the matching OrbitControls actions in that
pane only, composing with the existing scene-level `controls` mapping.

## Files

- Edit: `py/pytanga/viz/views.py` (import `CameraLock`, `SceneView` field + serialize)
- Edit: `py/pytanga/viz/templates/views/three-view.js` (apply lock per pane)
- Edit: `py/pytanga/viz/templates/view_mode.js` (add `applyCameraLock`, or fold into `configureControls`)
- Edit: `py/tests/viz/test_views.py` (or a new `test_camera_lock.py`)

## Steps

- [x] **3.1 — `SceneView.lock` + validation**
  - Add `lock: set[str] | None = None` to `SceneView.__init__`.
  - Normalize to a `frozenset`; validate each value with `CameraLock(v)`
    (raise `ValueError` for unknown parts). Keep `None`/empty as "no lock".

- [x] **3.2 — serialize**
  - In `SceneView._serialize`, emit `result["lock"] = sorted(self.lock)` only
    when non-empty (sorted for stable output).

- [x] **3.3 — frontend apply lock**
  - In `view_mode.js`, add `applyCameraLock(controls, lock)`:
    `rotate` → `controls.enableRotate = false`; `pan` → `controls.enablePan = false`;
    `zoom` → `controls.enableZoom = false` (and ensure no mouse button is mapped
    to DOLLY so scroll/drag zoom is truly disabled).
  - Call it after `configureControls` when the pane's scene_view node carries
    `lock`. Since `configureControls` currently doesn't set `enableZoom`, also
    set `controls.enableZoom = true` there (or in `applyCameraLock` default) so
    the unlocked path stays zoom-enabled.

- [x] **3.4 — per-pane wiring in `ThreeJsView`**
  - The `ThreeJsView` already receives the per-pane `camera` override; in the
    same place read the node's `lock` and apply it to this pane's controls only
    (do not touch other panes). Store it so layout re-push re-applies it.

- [x] **3.5 — tests**
  - `test_views.py`: `SceneView(lock={"rotate","pan"})` serializes
    `"lock": ["pan","rotate"]`; empty/None omitted; invalid value raises.
  - Optionally assert the scene_view node round-trips through `_serialize`.

## Validation

`uv run pytest py/tests/viz/test_views.py -q && node --check py/pytanga/viz/templates/view_mode.js && uv run python tools/build-viewer-js.py --check`

## Notes

- `enableZoom` is a standard `OrbitControls` flag but is not currently set by
  `configureControls` (which only sets `enableRotate`/`enablePan`); step 3.3
  makes the zoom lock explicit.
- Lock is intentionally per-pane (not per-scene) because both panes in the
  split view show the same scene.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
