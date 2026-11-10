# Phase 6 — Developer docs + branch changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Record the two contract changes phases 2–5 introduced — (a) the animated export
now skips entities by source-object identity and serializes frame application,
(b) `update<Kind>` may rewrite geometry in place — and add the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/dev/workflows/js-frontend-testing.md` (smoke + node-test
  registration, if phase 1 did not already add the smoke commands)
- New: `docs/changelog/2026/11/10_fix-anim-export-frame-skip.md`

## Steps

- [x] **6.1 — Architecture: export playback section**
  - In the paragraph that describes `_expandFrames` →
    `_reconcileFrame` (`viz-architecture.md`, ~lines 338-347), add:
    - the expander keeps a `state` Map, so **unchanged entities are the same
      object instance** in consecutive frames;
    - `_reconcileFrame` stores the last applied source object on
      `mesh.userData._src` / `entry.obj.userData._src` and skips an entity
      outright on an identity match (only `visible` is re-asserted) — i.e.
      per-frame work is proportional to what changed, and the hide loop stays
      "hide, don't dispose";
    - frame application is serialized by the pure `frame-pump.js`
      (`createFramePump(apply, onError)` → `request(n)` / `busy` / `idle()`):
      one apply in flight, newest target wins, so playback and scrubbing cannot
      interleave two reconciliations (`_figAnimate` is synchronous and only
      *requests* frames);
    - a legacy recording embedded as full `frames[]` has no object identity and
      therefore keeps the old whole-scene-per-frame behaviour (state it
      explicitly so nobody reads it as a bug).
  - Keep the existing prose about compressed data / `window.__tangaAnimReady`
    and the asset store intact — insert, do not rewrite.

- [x] **6.2 — Architecture: updater contract**
  - `viz-architecture.md` → "New entity kind" recipe step 5 (~lines 174-178):
    rewrite so an updater may (i) restyle in place **or** (ii) rewrite geometry
    in place (positions/colours, rebuilding an internal group) and return
    `true`; `return false` means "the representation changes or a rebuild is
    genuinely cheaper", and `styleNeedsRebuild(ent, prev)` is the style gate.
  - Add one sentence naming the kinds that own their decision now
    (`PointPath`, `Axis`, `Axes2D`, `Axes3D`, `Grid`, plus the existing `sdf`,
    `ray`, `image`, `depth_image`, `Line`, …) instead of falling through to the
    flat `entityRequiresRebuild` field list, and state the invariant that keeps
    it honest: an updater that returns `true` must leave the mesh fully
    consistent with `ent` (the caller then records `_data`/`_src` and re-applies
    the transform).
  - `docs/dev/guides/js-coding-style-guide.md`: extend the "unit-test pure
    modules" rule (lines 13-16) with `frame-pump.js` as the export-side example
    next to the existing `templates/views/reconcile.js` mention (~line 26) —
    it is a DOM-free module with a sibling `js/dev/tests/frame-pump.test.mjs`.

- [x] **6.3 — `js-frontend-testing.md` completeness check**
  - Confirm the phase-1 block is present (animated-export smoke, two
    terminals) and that the unit-test section mentions
    `frame-pump.test.mjs` / the "pure module" rule for the new pump.  Only edit
    what is missing.

- [x] **6.4 — Branch changelog**
  - New file `docs/changelog/2026/11/10_fix-anim-export-frame-skip.md`
    (branch changelog naming per `dev/workflows/changelog.md`; `10` =
    branch start day, `/` in the branch name → `-`).
  - Title from `uv run python tools/last-release.py` → currently
    `2.25.1 (2.26.0-rc1)`:
    ```markdown
    # Changes since version 2.25.1 (2.26.0-rc1)

    ## Bug Fixes
    - **Exported animations no longer rebuild unchanged entities** — the
      animated bootstrap skips any entity whose source frame object is identical
      to the one already applied, so static geometry, labels and axes stop being
      disposed and recreated on every frame.
    - **`PointPath` updates in place** — a changing path rewrites its
      fat-segment positions/colours instead of reallocating the mesh, keeping
      long traces cheap to animate in exported HTML and the live viewer alike.
    - **Axes and grids update in place** — `Axis`, `Axes2D`, `Axes3D` and
      `Grid` refill their existing group (or rewrite their segment positions)
      instead of rebuilding the entity, so changing tick labels no longer
      recreates the CSS2D label DOM every frame.
    - **Frame application is serialized** — a new `frame-pump.js` allows one
      frame apply in flight and lets the newest target win, so fast playback or
      scrubbing can no longer interleave two reconciliations.

    ## Refactor
    - **`update<Kind>` may rewrite geometry in place** — the documented renderer
      update contract now allows an updater to rebuild geometry and return
      `true`; `false` is reserved for a changing representation or a genuinely
      cheaper rebuild.
    ```
  - Do **not** touch `docs/changelog/index.md` yet — the index entry is added
    at PR time together with the hash rename (see `dev/workflows/pull-request.md`).
  - Wrap at ~80 columns, one self-contained sentence per bullet, matching the
    existing `docs/changelog/2026/11/09_7bd13e117.md` style.

## Validation

```bash
uv run mkdocs build --strict
uv run pytest py/tests/viz -q && (cd js/dev && npm test && npm run check)
node js/dev/tests/anim-export-smoke.mjs <url>
```

## Notes

- Final phase of the plan: after this, update the plan's `README.md` `Status:`
  line (per `dev/workflows/implement-plan.md`) and follow
  `dev/workflows/pull-request.md` for the squash + changelog rename + index
  entry.
- The changelog bullet list must stay user-visible-behaviour oriented; the
  `mesh.userData._src` / pump internals belong in the architecture doc, not in
  the changelog.
