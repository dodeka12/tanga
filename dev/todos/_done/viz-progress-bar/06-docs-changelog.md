# Phase 6 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Document the new control in the user docs and add the branch changelog.

## Files

- Edit: `docs/py/viz/ui/controls.md`
- Edit: `docs/py/viz/ui/control-views.md`
- New: `docs/changelog/2026/09/26_feat-ui-progress-bar.md`

## Steps

- [x] **6.1 — User docs**
  - `controls.md`: add `ProgressBarView` to the intro list and a
    `## ProgressBarView` section (determinate vs indeterminate, title/text,
    `set_progress`/`set_text`/`set_indeterminate`).
  - `control-views.md`: add `ProgressBarView` to the intro list; note it is
    read-only and updated via the existing `view.set_value` /
    `view.control.get_value()` runtime helpers.

- [x] **6.2 — Changelog**
  - Create `docs/changelog/2026/09/26_feat-ui-progress-bar.md` per
    `dev/workflows/changelog.md` (title `# Changes since version 2.11.0`,
    `## New Features` bullet).

## Validation

```bash
uv run mkdocs build --strict
```

## Notes

- Finalize the changelog filename to the hash form at PR time per
  `dev/workflows/pull-request.md`.
