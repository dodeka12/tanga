# Phase 3 — Reuse the group view (preserve title/collapse state)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make `group` reusable across a `view_layout` re-push so its collapse state (and
title/icon chrome) survive, while its children are re-parented like any other
container.  `split`/`stack`/`toolbar`/`menu` remain recreated.

Depends on Phase 2: `collapsed` is now backend-authoritative, so `update()`
applies the serialized `node.collapsed` instead of skipping it.

## Files

- Edit: `py/pytanga/viz/templates/views/reconcile.js`
- Edit: `py/pytanga/viz/templates/views/group-view.js`
- Edit: `py/pytanga/viz/templates/views/build.js`
- Edit: `js/dev/tests/reconcile.test.mjs`

## Steps

- [x] **3.1 — Add `group` to `REUSABLE_TYPES` (`reconcile.js`)**
  - Add `'group'` to the set and refresh the header comment (containers that
    remain rebuilt are now `split`/`stack`/`toolbar`/`menu`).

- [x] **3.2 — `GroupView.update(node)` (`group-view.js`)**
  - Add `update(node)` that refreshes `title`, `position`, `direction`,
    `collapsed`, `scrollable`, `gap`, `align`, `justify`, `icon`, `icon_only`,
    `tooltip`, `parent_id`, `groupId` with `??` fallbacks (apply `node.collapsed`
    — it is backend-authoritative after Phase 2).
  - Re-apply visual state without re-running `_setupChrome` (which would
    duplicate the header): call `_applyFlex()`, `_applyScroll()`,
    `_applyCollapsed()`, and update the title text / icon / toggle button in
    place (extract a small helper from `_setupChrome` if none exists).

- [x] **3.3 — Reuse branch in `build.js` (`group`)**
  - In the `group` branch (currently always `new GroupView(...)`), compute
    `existing = reuse.get(node.id)`; when present, clear its children first
    (`for (const c of [...existing.children]) existing.removeChild(c);`), then
    `existing.update(node); view = existing;` else construct fresh.
  - Keep `applySizeSpecs(view, node)` and re-add children via
    `view.addChild(buildViewTree(childNode, ws, reuse, registry, newScenes))`
    for both paths.
  - Note: `removeChild` unmounts (not destroys) the old children; reused leaf
    children are the same view objects and are re-attached by the child
    recursion.

- [x] **3.4 — Reconcile planner unit tests (`js/dev/tests/reconcile.test.mjs`)**
  - Add a test asserting `group` is **reused** on an id-stable re-push.
  - Add a test asserting `split`/`stack` are still **not** reused (rebuilt), to
    lock the container boundary.

## Validation

```
node js/dev/tests/check-syntax.mjs
node --test 'js/dev/tests/*.test.mjs'
```

## Notes

- `GroupView` retargets `this._content` to its inner `.tanga-group-content` div
  (see `_setupChrome`), so `StackView.addChild`/`removeChild` already mount
  children into the right element; reuse just needs the clear-then-rebuild
  ordering.
- Collapse state is the user-facing reason to preserve `group`; it is synced with
  the backend by Phase 2, so reuse preserves it and `update()` can trust
  `node.collapsed`.  Title/icon are static in practice but are refreshed for
  correctness.
