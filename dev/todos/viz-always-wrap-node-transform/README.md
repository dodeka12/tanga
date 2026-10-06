# Viz — always wrap entity meshes in a transform node — Overview

**Created:** 2026-10-05 | **Status:** Planned | **Branch:** `fix/html-export-transform`

## Goal

Make every scene entity render inside a per-entity `THREE.Group` transform node,
even when its `Transform` is the identity. Today `wrapWithNodeTransform` returns
the bare mesh for an identity transform, so `entry.obj === entry.mesh` and the
placement/geometry split breaks for those entities — the same split that caused
exported animations to drop per-frame transforms for in-place-updated entities.

## Architecture (short)

- `py/pytanga/viz/templates/scene-builder.js::wrapWithNodeTransform` currently
  short-circuits `if (isIdentityTransform(transform)) return mesh;`. Remove the
  short-circuit so it always builds `THREE.Group` → add mesh → apply transform.
- `buildSceneObject` tags the wrapper node with `entityId` + `kind` (mirroring
  `tagEntity`'s lightweight fields) so consumers that inspect
  `entry.obj.userData` — notably `interaction.js`'s image-deferral sort — keep
  working.
- The now-dead `entry.obj === entry.mesh` rebuild branch in
  `views/three-view.js::_updateEntityContent` is removed.
- Rebuild the committed CDN bundle (`js/tanga-viewer.js` + manifest).

## Decisions (confirmed)

- **Always wrap:** every scene entity gets a `THREE.Group`; `entry.obj` is always
  the wrapper and `entry.mesh` is always the inner geometry — no identity
  exception.
- **Tag the wrapper** with `entityId` + `kind` only (not the full `data` dict,
  which stays in `entry.data`).
- **Remove** the now-unused `isIdentityTransform` helper.
- **Remove** the dead `entry.obj === entry.mesh` branch in `_updateEntityContent`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-scene-builder-always-wrap.md](./01-scene-builder-always-wrap.md) | Always wrap + tag wrapper; regression test |
| 2 | [02-viewer-cleanup.md](./02-viewer-cleanup.md) | Remove dead `entry.obj === entry.mesh` branch |
| 3 | [03-rebuild-bundle.md](./03-rebuild-bundle.md) | Regenerate `js/tanga-viewer.js` + manifest |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Clarify architecture doc + branch changelog |

## Testing as you go

- Python: `uv run pytest py/tests/viz -q`
- JS syntax: `node js/dev/tests/check-syntax.mjs`
- JS unit: `node --test js/dev/tests/*.test.mjs`
- Bundle: `uv run python tools/build-viewer-js.py --check`
- Docs: `uv run mkdocs build --strict`

## Non-goals

- No change to the `Transform` data model, serialization, or the wire contract.
- No change to the animation reconcile transform-reapplication fix already on
  this branch (it is complemented by, but independent of, this change).
- No change to the static-export `meshMap` vs animated `figMeshMap` id→object
  mapping (inert; separate code paths).

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
> touches, so the new code aligns with the documented architecture. If this work
> introduces or changes architecture, update the developer docs.
