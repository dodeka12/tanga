# Phase 2 — Entity visibility (frontend)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Consume the `visible` field and the new `"visible"` aspect patch so the browser
actually hides/shows entities.

## Files

- Edit: `py/pytanga/viz/templates/scene-builder.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`

## Steps

- [x] **2.1 — `buildSceneObject` applies `visible` (`scene-builder.js`)**
  - After wrapping `mesh` into `node`, set
    `node.visible = (obj.visible !== false)`.

- [x] **2.2 — `_applyObjectPatch` handles `visible` (`three-view.js`)**
  - After the `transform`/`style` branches, add:
    `if (aspect === 'visible') { if (entry.obj) entry.obj.visible = value.visible !== false; return; }`

## Validation

```bash
node js/dev/tests/check-syntax.mjs
```

## Notes

- Live templates are served directly as ES modules; `build-viewer-js.py` only
  bundles the export library, so a syntax check is the gate here.
