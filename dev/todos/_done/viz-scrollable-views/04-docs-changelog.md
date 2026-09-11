# Phase 4 — Docs + changelog

## Goal

Document `scrollable` on the reference page and record the feature in the branch
changelog.

## Files

- Edit: `docs/py/viz/interaction/control-views.md`
- Edit: `docs/changelog/2026-08-31_fix-file-chooser-bug.md` (append)

## Steps

- [x] **4.1 — Reference docs**
  - In `control-views.md`, add `scrollable=False` to the `StackView` and
    `GroupView` signatures and a one-sentence note: with `scrollable=True` the
    container stops forcing its content size along the stack axis and scrolls
    inside the pane (thin dark scrollbar appears only on overflow).

- [x] **4.2 — Changelog**
  - Append a **New Features** bullet to the branch changelog
    `docs/changelog/2026-08-31_fix-file-chooser-bug.md` per
    `dev/workflows/changelog.md` (title already `# Changes since version 1.12.0`;
    re-verify with `uv run python tools/last-release.py`).

- [x] **4.3 — Full validation**
  - `uv run pytest py/tests/viz/ -q`
  - `node --test dev/src/js-tests/*.test.mjs`
  - `uv run mkdocs build --strict`

## Validation

`uv run pytest py/tests/viz/ -q && node --test dev/src/js-tests/*.test.mjs && uv run mkdocs build --strict`

## Notes

- The `docs/changelog/index.md` entry is added at PR time (after the hash-based
  rename) per `dev/workflows/pull-request.md` — not in this phase.
