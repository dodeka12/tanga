# Phase 4 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Update the architecture docs and the branch changelog for the range + menu
changes.

## Files

- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- New: `docs/changelog/2026/10/DD_fix-small-bugs.md`

## Steps

- [x] **4.1 — Architecture docs**
  - `viz-controls-and-interactions.md`: extend the `control_state` runtime-state
    section to document `min`/`max`/`step` (slider + value-edit) and the
    `set_control_range` / `set_range` API; note the menu auto-close behavior
    (buttons/dropdowns close; checkbox/slider stay open).

- [x] **4.2 — Changelog**
  - Create / append `docs/changelog/2026/10/DD_fix-small-bugs.md` per
    `dev/workflows/changelog.md` (title from `uv run python tools/last-release.py`;
    `## New Features` bullets for range mutation + menu auto-close).

## Validation

```bash
uv run mkdocs build --strict
```

## Notes

- Finalize the changelog filename to the hash form at PR time per
  `dev/workflows/pull-request.md`.
