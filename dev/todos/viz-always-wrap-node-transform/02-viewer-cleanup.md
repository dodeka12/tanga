# Phase 2 — Remove the dead `entry.obj === entry.mesh` rebuild branch

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`) for the
> subsystem(s) this work touches, so the new code aligns with the documented
> architecture. If this work introduces or changes architecture, update the
> developer docs.

## Goal

With always-wrap, `entry.obj === entry.mesh` can no longer be true for scene
objects, so the special rebuild branch in `_updateEntityContent` is dead. Remove
it, keeping only the wrapper-preserving path.

## Files

- Edit: `py/pytanga/viz/templates/views/three-view.js`

## Steps

- [ ] **2.1 — Replace the branch with the wrapper-preserving path**
  - In `_updateEntityContent` (currently lines 1275-1297), replace the
    `if (entry.obj === entry.mesh) { ... } else { ... }` block with:
    ```js
    removeEntityMesh(entry.mesh);
    entry.obj.add(newMesh);
    entry.mesh = newMesh;
    ```
    (Labels and attached groups ride on the wrapper `entry.obj`, so removing and
    re-adding only the inner mesh preserves them automatically.)

## Validation

```
node js/dev/tests/check-syntax.mjs
```

## Notes

- The removed branch's label/parent/attached-group re-wiring was only needed when
  `entry.obj` was the mesh itself (identity transform); the wrapper path handles it
  implicitly.
