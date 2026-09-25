# Phase 3 — Extract the reconciliation core into a DOM-free module

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make the layout reconciliation / orphan-map accounting **unit-testable without a
browser** by extracting it into a pure module (no `document`, no `three`) and
refactoring `buildViewTree` to use it. This is the enabling step for the
`node --test` unit tests in Phase 4, and it codifies the "frontend logic must be
testable headlessly" policy.

## Files

- New: `py/pytanga/viz/templates/views/reconcile.js` (pure)
- Edit: `py/pytanga/viz/templates/views/build.js` (use it)

## Steps

- [x] **3.1 — `views/reconcile.js` (pure, no DOM/three imports)**
  - `collectNodeTypes(root)`: DFS over `node` + `node.children` (+ `overlay`
    children), returning `[{ id, type }]` in traversal order.
  - `planReconciliation(nodes, live /* Map<id, typeTag> */)`:
    - a node whose `id` exists in `live` **and** `live.get(id) === node.type`
      is a **reuse** (and is removed from a working copy of `live`);
    - otherwise the node is a **create**;
    - whatever remains in `live` after the walk is the **orphaned** set.
    - Return `{ reuse: [{id, type}], create: [{id, type}], orphaned: [id] }`.
  - This is the exact accounting `buildViewTree` currently does inline, now
    operating on plain strings/maps.

- [x] **3.2 — Refactor `buildViewTree` (`build.js`)**
  - Add a `view.typeTag = node.type` stamp in `registerView` (alongside
    `view.viewId`), and tag the `reuse` registry views with their `typeTag` when
    they are registered.
  - Build `live = new Map([...reuse].map(([id, v]) => [id, v.typeTag]))`, run
    `planReconciliation(collectNodeTypes(root), live)`, and use its
    `reuse`/`create`/`orphaned` result to drive the existing per-type
    reuse-vs-construct branches (replacing the inline
    `reuse.get(node.id)` + `instanceof` checks).
  - Behaviour must be identical: reuse by id **and** type, create new ids, and
    leave orphans for `_buildLayout` to destroy.

- [x] **3.3 — Smoke**
  - Run the Python viz suite; confirm the live frontend still reconciles
    (no regressions in serialization/tests).

## Validation

```
uv run pytest py/tests/viz -q
# In the node clone: node --check py/pytanga/viz/templates/views/reconcile.js
```

## Notes

- Keep `reconcile.js` import-free of `three`/`view.js`/`controls-panel.js` — it
  must load in plain Node for `node --test`.
- The `instanceof` type check moves to a string `typeTag` comparison, which is
  what lets the planner be pure; the DOM classes stay in `build.js`.
