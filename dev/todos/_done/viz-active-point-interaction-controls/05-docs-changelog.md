# Phase 5 — Developer docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`).
> Update the developer docs to reflect the new public API and the button-scoped
> navigation yield.

## Goal

Document the new public API and the button-scoped navigation yield, and add a
branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- New: `docs/changelog/2026/10/DD_feat-active-elements.md`
- Edit: `docs/changelog/index.md` (deferred to PR time)

## Steps

- [x] **5.1 — Update the architecture doc.**
  - In `docs/dev/architecture/viz-controls-and-interactions.md`, in the
    "Per-handler enable/disable + cursors" and "Active rectangles" /
    `InteractionSurface` sections, document `ActPoint.set_drag_modifiers(*modifiers)`
    and the composite `set_handles_enabled` / `set_handles_visible` bulk API, and
    note the frontend `InteractionController.armedSurfaceButtons()` button-scoped
    yield.
- [x] **5.2 — Changelog.**
  - Create `docs/changelog/2026/10/DD_feat-active-elements.md`
    per `dev/workflows/changelog.md`: title from `uv run python tools/last-release.py`;
    sections `## New Features` (handle controls + modifier gating) and
    `## Bug Fixes` (right-button pan blocked while a draw mode is armed).
- [x] **5.3 — Changelog index (deferred).**
  - The `docs/changelog/index.md` entry is added at PR time, after the
    hash-based rename, per `dev/workflows/changelog.md` § Index update — not on
    the feature branch.

## Validation

`uv run mkdocs build --strict`

## Notes

- The changelog filename uses `DD_` + branch name with `/`→`-`; the PR-time hash
  rename happens later (see `dev/workflows/pull-request.md`).
