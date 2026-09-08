# Phase 5 — Architecture docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Align the architecture doc with the new factory location and record the refactor
in the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- Edit: `docs/changelog/2026-09-07_fix-misc.md`

## Steps

- [x] **5.1 — Update the architecture doc**
  - In `viz-controls-and-interactions.md` step 3 ("Frontend"), change
    "add a `create<Kind>` factory in `templates/controls-panel.js`" to
    "add a `create<Kind>` factory in `templates/controls/<kind>.js` (importing
    the shared registry/event/icon helpers from `controls-panel.js`)".

- [x] **5.2 — Add a changelog entry**
  - Append a `## Refactor` section to `docs/changelog/2026-09-07_fix-misc.md`
    (per `dev/workflows/changelog.md`) with one bullet: the per-control DOM
    factories moved from `controls-panel.js` to `controls/<x>.js`, and the
    orphaned `createFileChooser` was removed.

## Validation

`uv run mkdocs build --strict`

## Notes

- `docs/changelog/index.md` is updated at PR time (see
  `dev/workflows/pull-request.md`), not here.
