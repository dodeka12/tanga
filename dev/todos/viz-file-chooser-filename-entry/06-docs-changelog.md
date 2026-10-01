# Phase 6 — Docs + changelog

## Goal

Document the new file-chooser behavior and record the change in the changelog.

## Files

- Edit: `docs/dev/architecture/viz-controls-and-interactions.md` (file-chooser paragraph)
- Edit: `docs/py/viz/example-apps/image-labeling-app.md` (Save As behavior)
- Edit: `docs/changelog/2026/09/30_feat-calibrated-pane-interaction.md` (branch changelog)
- Regenerate: `docs/py/examples/apps/image_labeling_app.md` (via tool)

## Steps

- [x] **6.1 — Architecture doc**
  - Update the **File chooser** paragraph to state: the dialog footer is an
    editable filename field; the typed filename is used as a case-insensitive
    glob (`pattern`) filter over the selected folder; `existing_only` (default
    true) controls whether a non-existent filename may be accepted; OK sends the
    full path as the `accept` `value`.
- [x] **6.2 — Example docs**
  - In `image-labeling-app.md`, note Save As… allows a new filename (`.json`
    appended when missing) and Open… requires an existing file.
- [x] **6.3 — Regenerate example docs**
  - Run `uv run python tools/generate-example-docs.py` and `--check`.
- [x] **6.4 — Changelog**
  - Append a `## New Features` bullet (and any `## Bug Fixes`) to the branch
    changelog following `dev/workflows/changelog.md`; do not renumber or invent
    a version (title stays `# Changes since version 2.12.1`).

## Validation

```
uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict
```

## Notes

- `tools/last-release.py` currently prints `2.12.1`; keep the changelog title
  matching it.
- `docs/py/viz/example-apps/image-labeling-app.md` is hand-written (referenced
  from `mkdocs.yml`); `docs/py/examples/apps/image_labeling_app.md` is generated
  from the `.py`.
- `mkdocs build --strict` passes.  `generate-example-docs.py --check` still
  reports **pre-existing** drift for `apps/calibrated_labeling_app.md` (the
  branch edited that example's `.py` without regenerating its doc); it is
  unrelated to this phase and left out of the commit.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
