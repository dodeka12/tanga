# Phase 4 — Docs + changelog

## Goal

Document the measured `GroupView` chrome and its theme-tracking behavior, then
append the fix to the branch changelog and run the full validation gate.

## Files

- Edit: `docs/py/viz/visualizer/split-views.md`
- Edit: `docs/changelog/2026-09-02_feat-viz-layout-sizing.md` (append)
- Edit: `docs/changelog/index.md` (only if the summary line changes)

## Steps

- [x] **4.1 — Document the sizing behavior.**
  - In `split-views.md`, note that a `GroupView` reports its `preferred_height`
    as content plus the title-bar/panel chrome (measured from the rendered DOM,
    so it follows the active theme), and that a collapsed group is sized to the
    title bar's bottom border.

- [x] **4.2 — Changelog.**
  - Per `dev/workflows/changelog.md`, append a **Bug Fixes** bullet to the
    existing branch changelog
    `docs/changelog/2026-09-02_feat-viz-layout-sizing.md` describing the
    `GroupView` preferred-height + folded-height fix.
  - Update `docs/changelog/index.md`'s `[Since 1.16.0]` entry only if the
    summary line needs the new fix mentioned.

- [x] **4.3 — Full validation.**
  - Run the whole gate below.

## Validation

```powershell
uv run pytest py/tests/viz/ -q
node --test 'dev/src/js-tests/*.test.mjs'
uv run python tools/generate-example-docs.py --check
uv run mkdocs build --strict
```

## Notes

- The changelog is the same file created by `viz-layout-sizing` phase 5 (the
  branch is unmerged); append, don't create a new one. It is renamed to the
  hash form at PR time per `dev/workflows/pull-request.md`.
