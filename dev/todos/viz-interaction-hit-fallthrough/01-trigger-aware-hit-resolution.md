# Phase 1 — Trigger-aware hit resolution

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> — the "Interaction surface" section).  This phase changes the frontend
> hit-arbitration; the doc update lands in Phase 2.

## Goal

Extract pure trigger-matching and hit-resolution helpers, rewire the four gesture
call sites to walk hits nearest→furthest (surface last), add a unit test, and
regenerate the bundle.

## Files

- New: `py/pytanga/viz/templates/hit-resolution.js`
- Edit: `py/pytanga/viz/templates/interaction.js`
- New: `js/dev/tests/hit-resolution.test.mjs`

## Steps

- [x] **1.1 — Pure `matchTriggers(config, eventType, button, modifiers)` (`hit-resolution.js`).**
  - Move the trigger-filter body of `_findMatchingTriggers` into a pure exported
    function; keep `_findMatchingTriggers` as a thin wrapper that does
    `this._getObjectConfig(objectId)` then calls `matchTriggers`.
  - Fix the latent bug: match modifiers **exactly** (a trigger with no
    `modifiers` fires only when no modifiers are held), and update the
    `surfaceClaimsPointer` comment accordingly.

- [x] **1.2 — Pure `resolveHitTarget(candidates, surface, getConfig, eventType, button, modifiers)`.**
  - Return the first `{objectId, intersect}` in `candidates` (nearest→furthest)
    whose config has a matching trigger; if none, return `surface` when its config
    matches; else `null`.  `getConfig(id)` is injected so the function stays pure.

- [x] **1.3 — Refactor `_getInteractiveHit` to return the full sorted hit list.**
  - Keep the image-plane-last mesh sort; map every `intersects[i]` back to its
    registered `objectId` (via the existing `_isDescendantOf` walk), deduping by
    `objectId` (keep the nearest hit per object), and return the list.

- [x] **1.4 — Add `_resolveGestureHit(eventType, button, modifiers)` to the controller.**
  - Build `candidates` from `_getInteractiveHit`, `surface` from `_getSurfaceHit`,
    and call `resolveHitTarget(..., (id) => this._getObjectConfig(id), ...)`.

- [x] **1.5 — Rewire the four gesture sites.**
  - `_onPointerDown`: compute `button`/`modifiers` first; resolve the **drag**
    target to start a drag, and the **click** target to seed `_clickState`.
  - `_onPointerUp`: resolve the **click** target and match `_clickState` by it.
  - `_onDblClick`: resolve with `'dblclick'`.
  - `_onWheel`: resolve with `'scroll'`.

- [x] **1.6 — Unit test (`js/dev/tests/hit-resolution.test.mjs`).**
  - Cover: nearest matching entity wins; a nearer non-matching entity passes to a
    farther matching one; surface wins when no entity matches; surface declines →
    `null`; modifier/button matching is exact (empty = no modifiers).

- [x] **1.7 — Confirm the export bundle is unaffected.**
  - `interaction.js` is a live-viewer module (not in `_RENDERER_FILES`/
    `_SHARED_JS_FILES`), so no bundle rebuild is needed; run
    `uv run python tools/build-viewer-js.py --check` to confirm no drift.

## Validation

`node --test js/dev/tests/*.test.mjs && node js/dev/tests/check-syntax.mjs && uv run python tools/build-viewer-js.py --check`

## Notes

- Hover (`_onPointerMove` at `interaction.js:717`) already uses `_getInteractiveHit`
  directly and must stay untouched.
- The drag pipeline reuses `this._activeDrag.objectId` captured at pointerdown, so
  only the target choice changes — drag_start/move/end payload building is unchanged.
- Manual browser smoke (Playwright) for the actual behavior is separate, per
  `js/dev/README.md`.
