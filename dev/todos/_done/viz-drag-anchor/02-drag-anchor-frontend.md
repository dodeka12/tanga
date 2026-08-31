# Phase 2 — Frontend: send the ray, handle the anchor, rebase

## Goal

Send the picking ray with `drag_start`, receive `interaction:drag_anchor`, and
rebase both the drag accumulation and the pixel→world scale onto the ideal
anchor so `world_position` never carries the mesh-surface offset (or a
wrong-depth drag speed).

## Files

- Edit: `py/pytanga/viz/templates/interaction.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`

## Steps

- [x] **2.1 — Capture the ray and add anchor state at pointerdown**
  - In `_onPointerDown`, when a drag trigger matches, store the world-space ray
    from `this.raycaster.ray` into `_activeDrag`:
    `rayOrigin: [this.raycaster.ray.origin.x, this.raycaster.ray.origin.y,
    this.raycaster.ray.origin.z]` and the analogous `rayDirection` from
    `this.raycaster.ray.direction`.
  - Add `anchorPending: true` and `pendingPixelDelta: new THREE.Vector2()` to
    `_activeDrag` (buffers raw screen-pixel deltas, not world units).

- [x] **2.2 — Extract a pure pixel→world conversion helper**
  - Factor the inline conversion in `_onPointerMove` (the
    `_axisMappedDelta(...)` branch and the
    `rawDelta.addScaledVector(screenDx, dx).addScaledVector(screenDy, dy)` +
    `_projectToPlane(...)` fallback) into
    `_pixelToWorldDelta(dx, dy, screenDx, screenDy, dragMode)` returning a
    `THREE.Vector3`.  `_onPointerMove` calls it instead; the math is unchanged,
    only relocated.

- [x] **2.3 — Send the ray on `drag_start`; buffer pixels until anchored**
  - In `_onPointerMove`, add `ray_origin` / `ray_direction` to `basePayload`
    only when `eventType === 'drag_start'`, reading them from
    `this._activeDrag.rayOrigin` / `rayDirection` (captured at pointerdown in
    step 2.1 — do not read `this.raycaster.ray`, which is reused for hover on
    `pointermove`).
  - While `_activeDrag.anchorPending`, accumulate the raw pixel deltas
    (`_activeDrag.pendingPixelDelta.x += dx`, `...y += dy`) and skip the
    world-space block entirely — except the very first move still sends the
    `drag_start` (its `world_position` stays the pointerdown hit point and
    `world_delta` is `[0, 0, 0]`, the pre-anchor best-effort value).
  - Once `anchorPending` is false, behave exactly as today: convert via
    `_pixelToWorldDelta`, accumulate `accWorldPos`, send `drag_move`.

- [x] **2.4 — Add `setDragAnchor(objectId, worldPosition)`**
  - New public method on `InteractionController`:
    - Guard: `_activeDrag` exists, `objectId` matches, and `anchorPending`.
    - `const anchor = new THREE.Vector3(worldPosition[0], worldPosition[1],
      worldPosition[2])`.
    - Recompute the screen-plane vectors at the anchor:
      `const { screenDx, screenDy, dist } =
      this._computeScreenPlaneVectors(anchor)`.
    - Convert the buffered pixels once at the anchor's scale:
      `const worldDelta = this._pixelToWorldDelta(
      this._activeDrag.pendingPixelDelta.x, this._activeDrag.pendingPixelDelta.y,
      screenDx, screenDy, this._activeDrag.dragMode)`.
    - `_activeDrag.accWorldPos.copy(anchor).add(worldDelta)`.
    - Update `_activeDrag.screenDx = screenDx`,
      `_activeDrag.screenDy = screenDy`, `_activeDrag.dist = dist` so
      subsequent moves use the anchor's scale.
    - Clear `anchorPending`.
    - Send one immediate `drag_move` with the corrected `world_position`
      (reuse the existing payload builder, bypassing the throttle for this one
      send).

- [x] **2.5 — Route `interaction:drag_anchor` to the controller**
  - In `three-view.js` `handleMessage`, add:
    `else if (msg.type === 'interaction:drag_anchor')` →
    `this._interaction.setDragAnchor(msg.object_id, msg.world_position);`

- [x] **2.6 — Confirm drag-end cleanup**
  - `_onPointerUp` / `_cancelDrag` already null `_activeDrag`; verify the new
    fields (`rayOrigin`, `rayDirection`, `anchorPending`, `pendingPixelDelta`)
    need no extra cleanup and are dropped with `_activeDrag`.

## Validation

`node --check py/pytanga/viz/templates/interaction.js && node --check py/pytanga/viz/templates/views/three-view.js && uv run pytest py/tests/viz -q`

## Notes

- The pixel→world conversion is deferred until the anchor arrives, so the
  screen-plane vectors are computed at the anchor's depth
  (`_computeScreenPlaneVectors(anchor)`), not the hit point's.  For an
  orthographic (2D) camera this is a no-op; for a perspective camera it keeps
  the drag speed correct for positive-dimensional actives (circle/sphere).
- `_pixelToWorldDelta` is a pure helper (no DOM/`THREE.Raycaster`) — the same
  `_axisMappedDelta` / `_projectToPlane` math, just relocated and reused by
  `setDragAnchor`.
- If `pointerup` arrives while `anchorPending`, the drag simply ends without
  moving (the anchor never arrived); acceptable fallback.
