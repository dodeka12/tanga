# Phase 1 — Always wrap entity meshes in a transform node

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md` →
> "Canonical frame + transform placement") for the subsystem this work touches, so
> the new code aligns with the documented architecture. If this work introduces or
> changes architecture, update the developer docs.

## Goal

Make `wrapWithNodeTransform` always create and return a `THREE.Group` (no identity
short-circuit), tag the wrapper node with `entityId` + `kind`, and add a Python
regression test asserting the generated library always wraps.

## Files

- Edit: `py/pytanga/viz/templates/scene-builder.js`
- New: `py/tests/viz/test_scene_builder_wrap.py`

## Steps

- [ ] **1.1 — Always wrap in `wrapWithNodeTransform`**
  - Replace the body (currently lines 28-34) so it always builds the node:
    ```js
    export function wrapWithNodeTransform(mesh, transform) {
        const node = new THREE.Group();
        node.add(mesh);
        if (transform) applyTransformToObject(node, transform);
        return node;
    }
    ```
- [ ] **1.2 — Remove the now-unused `isIdentityTransform`**
  - Delete the `export function isIdentityTransform(...)` block (currently lines
    11-19).
- [ ] **1.3 — Tag the wrapper node with identity**
  - In `buildSceneObject`, after `node.userData.parentId = obj.parent_id || null;`,
    add:
    ```js
    node.userData.entityId = obj.id;
    node.userData.kind = obj.kind;
    ```
    so `interaction.js`'s image-deferral sort (which reads `userData.kind` off
    `entry.obj`) keeps working.
- [ ] **1.4 — Add a regression test**
  - New `py/tests/viz/test_scene_builder_wrap.py` asserting, on
    `generate_library_js()`:
    - `"isIdentityTransform" not in js`
    - `"function wrapWithNodeTransform(mesh, transform)" in js`
    - `"node.userData.kind = obj.kind" in js`
    - `"node.userData.entityId = obj.id" in js`

## Validation

```
node js/dev/tests/check-syntax.mjs
uv run pytest py/tests/viz/test_scene_builder_wrap.py -q
```

## Notes

- The documented architecture already states "the per-entity `THREE.Group` that
  already wraps each mesh" (`viz-architecture.md`, "Canonical frame + transform
  placement"); this phase makes the code match that invariant.
- Tag the wrapper with `entityId`/`kind` only — do **not** copy the full `data`
  dict (it already lives in `entry.data`).
