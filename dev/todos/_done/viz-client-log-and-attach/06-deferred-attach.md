# Phase 6 — Deferred `parent_id` attach fix

## Goal

Make a `GroupView(..., parent_id=…)` in a `SceneView(overlay=[...])` appear on
first load by deferring the CSS2D attach until the parent entity exists, instead
of dropping it when the layout builds before the scene entities.

## Files

- Edit: `py/pytanga/viz/templates/views/three-view.js`

## Steps

- [x] **6.1 — Queue instead of drop**
  - Add `this._pendingAttachedGroups = new Map()` in the `ThreeJsView`
    constructor (beside `this._overlays`).
  - In `addOverlay`, when `view.parent_id` is set but
    `this.sceneObjects.get(view.parent_id)?.obj` is missing, push `view` into
    `_pendingAttachedGroups` (list per parent id) and `sendLog('debug', …,
    { source: 'three-view.js', data: { parent_id } })` instead of the current
    `console.warn` + return. Still return `view`.

- [x] **6.2 — Attach on entity arrival**
  - In `_upsertObject`, after `const entry = await buildSceneObject(msg, this.scene, this.sceneObjects);`
    (scene-layer branch), drain `this._pendingAttachedGroups.get(msg.id)` and
    `attachGroupView(group, entry.obj)` for each queued group, then delete the
    pending entry. Guard on `entry && entry.obj`.

- [x] **6.3 — Clean up pending state**
  - `clearAll()`: add `this._pendingAttachedGroups.clear()` next to `detachAll()`.
  - `clearOverlays()`: also detach CSS2D-attached groups belonging to this
    pane's scene objects (iterate `this.sceneObjects`, `detachGroup` each
    `entry.obj.userData._attachedGroups` id) and clear `_pendingAttachedGroups`,
    so a layout re-push that reuses the pane doesn't leak or double-attach.

## Validation

`node --check py/pytanga/viz/templates/views/three-view.js && node --test 'dev/src/js-tests/*.test.mjs'`

Manual smoke: `uv run python py/examples/viz/ui/controls/control_group_single.py`
— the "Sphere" opacity group must render above the sphere and the slider must
still dispatch.

## Notes

- Deferral is now *expected* on first load (the layout always arrives before the
  entities), so it is reported at `debug`, not `warn`.
- The `console.warn` at `three-view.js:151` is removed by 6.1 (superseded by
  `sendLog` + deferral); keep the `attachGroupView`/`detachGroup`/`detachAll`
  API in `controls-attached.js` unchanged.
