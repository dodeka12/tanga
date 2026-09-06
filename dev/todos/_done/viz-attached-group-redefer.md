# Fix: attached control group vanishes when an entity's mesh is rebuilt

**Created:** 2026-09-05 | **Status:** Done | **Branch:** `fix/examples`

## Goal

When an entity with an attached `GroupView(parent_id=...)` is updated by
rebuilding its mesh — e.g. `viz.update_entity("sphere", Sphere(...))` changes
the radius — the attached group must survive. Today `removeEntityMesh` deletes
the group's CSS2D element and leaves its `CSS2DObject` parented to the discarded
mesh, so the group disappears. Re-defer orphaned groups into
`ThreeJsView._pendingAttachedGroups` (the existing delayed-attach map) instead,
and keep the hard `detachGroup` only for the actual delete path.

## Root cause (short)

- A radius change is a `content` patch → `_updateEntityContent` rebuilds the
  mesh; a kind change is a `full` patch → `_upsertObject` rebuilds it.
- `removeEntityMesh` (`renderers/factory.js`) traverses the old mesh and removes
  every CSS2DObject child's DOM element; the attached group's `CSS2DObject`
  stays parented to the discarded old mesh → orphaned.
- The update paths only re-attach `_labels` (branch A), never `_attachedGroups`.
- `_removeSceneObject` already `detachGroup`s on an actual delete — that path is
  correct and must stay.

## Decisions (confirmed)

- Reuse the delayed-attachment map: an **update** (rebuild) re-defers the
  attached groups into `_pendingAttachedGroups`; an **actual delete**
  (`_removeSceneObject`) keeps hard `detachGroup`. The update-vs-delete decision
  is encoded at the call site, so no boolean flag is added to `removeEntityMesh`.
- `attachGroupView` stores the `groupView` in its `_attachedGroups` entry so a
  released group can be re-attached later via `attachGroupView`.

## Steps

- [x] **1 — `attachGroupView` keeps the `groupView`** (`controls-attached.js`)
  - Change the stored entry (line 36) to
    `_attachedGroups.set(groupId, { css2d, parentMesh, groupView });`.
  - Update the `_attachedGroups` comment (line 12) to mention `groupView`.

- [x] **2 — `releaseAttachedGroups(parentMesh)`** (`controls-attached.js`)
  - Add an export that iterates `parentMesh.userData._attachedGroups`, does
    `entry.css2d.removeFromParent()` (soft — keeps `.element`), deletes the
    `_attachedGroups` entry, clears `parentMesh.userData._attachedGroups`, and
    returns `[{ groupId, groupView }]`.

- [x] **3 — `ThreeJsView` re-defer + drain helpers** (`three-view.js`)
  - Add `_redeferAttachedGroups(obj)`: call `releaseAttachedGroups(obj)` and push
    each `groupView` into `_pendingAttachedGroups[groupView.parent_id]`.
  - Add `_attachPendingGroups(id, obj)`: extract the existing drain loop
    (lines 594-597) so it is reusable.
  - Update the import (line 15) to also bring in `releaseAttachedGroups`.

- [x] **4 — Wire the update paths** (`three-view.js`)
  - `_upsertObject` (line 574): before `removeEntityMesh(old.obj)` (line 578),
    call `this._redeferAttachedGroups(old.obj)`; replace the inline drain
    (594-597) with `this._attachPendingGroups(msg.id, entry.obj)`.
  - `_updateEntityContent` branch A (lines 677-691): call
    `this._redeferAttachedGroups(entry.obj)` before `removeEntityMesh(entry.obj)`
    (line 678), and `this._attachPendingGroups(id, newMesh)` after re-adding
    `newMesh` (next to the `_labels` loop). Branch B (line 692) is unchanged —
    the wrapper `entry.obj` survives, so the group is never orphaned there.

## Validation

`node --check py/pytanga/viz/templates/controls-attached.js && node --check py/pytanga/viz/templates/views/three-view.js && node --test 'dev/src/js-tests/*.test.mjs'`

Manual smoke: `uv run python py/examples/viz/ui/controls/control_group_single.py`
— drag the **radius** slider (the "Sphere" opacity group must stay attached);
drag **opacity** (style path, must keep working); click **Reset**.

## Notes

- No change to `removeEntityMesh` or `_removeSceneObject`; the delete path is
  already correct.
- `attachGroupView` re-creates the `CSS2DObject` on re-attach; the released
  element stays in the DOM and is re-appended by `CSS2DRenderer` on the next
  frame.
