# Phase 2 — Skip entities whose source object is unchanged

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make `_reconcileFrame` treat "same source frame object as last applied" as
"nothing to do": no `updateEntityMesh` call, no `applyTransformToObject`, no
dispose/recreate.  This alone removes every rebuild of a static entity — the
bulk of the defect — because `_expandFrames` already hands out the *same*
object instance for entities that did not change.

## Files

- Edit: `py/pytanga/viz/export/_bootstrap/_animation.py` (`js_reconcile_frame`)
- New: `py/tests/viz/test_export_animation_frame_skip.py`

## Steps

- [x] **2.1 — Scene-entity guard + `_src` bookkeeping**
  - Insert the guard directly after the `if (!mesh) { … continue; }` create
    branch and **before** `const prev = mesh.userData._data || {};` — i.e.
    ahead of the `image` special case, so an unchanged image frame is skipped
    too:
    ```js
    // Nothing about this entity changed since it was last applied: the
    // expander hands out the same object instance for unchanged entities, so
    // an identity match means "already correct" — only re-assert visibility.
    if (mesh.userData._src === ent) {
        mesh.visible = true;
        continue;
    }
    ```
  - Assign `mesh.userData._src = ent` (the **frame object**, never the merged
    dict) in every apply path:
    - create branch, next to `entry.mesh.userData._data = ent;`
    - in-place branch, after `mesh.userData._data = { ...prev, ...ent };`
    - `image` rebuild branch: `newEntry.mesh.userData._src = ent;`
    - generic rebuild branch: `newEntry.mesh.userData._src = ent;`
  - The assignment target in a rebuild branch must be `ent`, **not** the local
    `merged` dict: `merged` is a fresh object that never appears in `frames[]`,
    so `_src = merged` would make every following frame look changed.
  - Remember this block is emitted from an **f-string**: literal braces need
    `{{` / `}}` (no new braces are introduced by these statements).
  - Extend the `js_reconcile_frame` docstring: record the invariant
    ("`mesh.userData._src` holds the exact frame object last applied; an
    identity match means the mesh already reflects it") and note that the hide
    loop only flips `visible`, so a hidden-then-returning entity is compared
    against the object it was built from.

- [x] **2.2 — Overlay-entity guard (same rule, both branches)**
  - In the `ent.layer === 'overlay'` branch, after the `if (!entry) { … }`
    create block and before the `entry.obj.visible = true;` re-assertion:
    ```js
    if (entry && entry.obj.userData._src === ent) continue;
    ```
  - Set `entry.obj.userData._src = ent` once, in the `if (!entry)` create block
    (the overlay branch has no in-place update path — it only re-asserts
    `visible` / `element.style.display`), so exactly one assignment is emitted.
  - Rationale: labels arrive as one *overlay* entity each and are unchanged for
    the whole recording in the common case; without this they are re-touched
    every frame.  Keep the rule identical to the scene branch so there is one
    concept to understand.

- [x] **2.3 — Python regression test (`test_export_animation_frame_skip.py`)**
  - Header: SPDX + copyright, module docstring explaining that the reconcile
    engine is a Python-emitted JS string, so the test guards the *emitted
    contract* (`node` is not available in CI, which is Python-only — the
    behavioural gate is `js/dev/tests/anim-export-smoke.mjs`).
  - `js = js_reconcile_frame(scene_var="figScene")` (module constant or small
    fixture); assert:
    - `"mesh.userData._src === ent" in js`, and its index is **smaller** than
      `js.index("updateEntityMesh(")` (guard must precede the update call) and
      smaller than `js.index("ent.kind === 'image'")` (images skipped too);
    - `js.count("mesh.userData._src = ent") == 4` — one per scene apply path
      (create, in-place, image rebuild, generic rebuild); note the overlay
      assignment uses `obj.userData`, so it does not inflate this count;
    - `"userData._src = merged" not in js` — the merged-dict trap;
    - `"entry.obj.userData._src === ent" in js` and
      `js.count("obj.userData._src = ent") == 1` (overlay).
  - Second test — identity precondition on the expander: import
    `js_expand_frames` and assert the emitted body still stores objects
    (`"for (const ent of initial) state.set(ent.id, ent);"` and the
    `d.set` loop `state.set(ent.id, ent)`), i.e. unchanged entities keep their
    identity — if this ever changes, the skip silently stops working.
  - Third test — the hide loops stay "hide, not dispose":
    `"if (!targetIds.has(id)) mesh.visible = false;" in js`, and
    `removeEntityMesh` appears only in the rebuild branches (pin the count).

## Validation

```bash
uv run pytest py/tests/viz/test_export_animation_frame_skip.py -q \
  && uv run pytest py/tests/viz -q \
  && (cd js/dev && npm run check)
node js/dev/tests/anim-export-smoke.mjs <url>   # terminal 2, generator from phase 1
```

Smoke expectation after this phase: the `removed`/`created` deltas drop from
the baseline to near zero (only genuinely re-represented entities rebuild),
while `updated` stays non-zero.

## Notes

- Why identity is enough: `_expandFrames` builds `frames[]` once from
  `initial` + `deltas` and reuses the **same** `ent` object for every frame an
  entity is unchanged in (`state` Map).  The `frames[n]` arrays themselves are
  new each frame, but their members are shared.  Legacy recordings
  (`animData.frames` present) pass through untouched and keep today's
  behaviour — no identity, no skip.
- Why store on `mesh.userData`: it dies with the mesh (no leak, no id-keyed
  side map to keep in sync) and it needs no new bootstrap declarations or
  bridge symbols.
- Do **not** move the guard above the `if (!mesh)` create branch: a first-seen
  entity has no `_src` and must be built.
