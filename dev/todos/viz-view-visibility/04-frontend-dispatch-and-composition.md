# Phase 4 — Frontend dispatch, build gate, and visibility composition

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Apply the three-condition visibility model in the live viewer: dispatch the
`view_visibility` message, skip construction outside an entity's `visible_in`
scope, and compose global `visible` with the per-view runtime toggle.

## Files

- Edit: `py/pytanga/viz/templates/viewer.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`

## Steps

- [x] **4.1 — Dispatch `view_visibility`**
  - In `viewer.js`, next to the other `view_*` branches, add:
    `if (msg.type === 'view_visibility') { const t = _viewById.get(msg.view_id); if (t) t.setVisibility(msg.hide); return; }`
- [x] **4.2 — Static scope gate**
  - Add `_inStaticScope(msg)` = `!msg.visible_in || msg.visible_in.length === 0 || msg.visible_in.includes(this.viewId)`.
  - In `_upsertObject` scene branch, replace the `_isFilteredOut` early return with
    `if (!this._inStaticScope(msg)) return;`.
- [x] **4.3 — Visibility composition**
  - Add `_applyVisibility(entry)` = `entry.obj.visible = (entry.data.visible !== false) && !this._hide.has(entry.data.id)`.
  - Call it after `buildSceneObject` in `_upsertObject`; after `entry.data = …` in
    `_updateEntityContent`; and in `_applyObjectPatch`'s `visible` branch (also set
    `entry.data.visible` there).
- [x] **4.4 — Runtime toggle**
  - Add `setVisibility(hide)` = `this.setVisibilityFilter(hide, null)` then
    reconcile every `sceneObjects` entry via `_applyVisibility`.
  - `_isFilteredOut` is now used only for composition, not build gating.

## Validation

`node js/dev/tests/check-syntax.mjs && node --test 'js/dev/tests/*.test.mjs'`
