# Phase 6 — Developer docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`).
> Update the developer docs to reflect the `ActiveObject` rename and the unified
> handle API.

## Goal

Document the `ActiveObject` base, the `ActPoint` active/content styles, and the
unified `set_handles_*` / `set_drag_modifiers` API, and add a branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- New: `docs/changelog/2026/10/DD_feat-active-object-unification.md`
- Edit: `docs/changelog/index.md` (deferred to PR time)

## Steps

- [x] **6.1 — Update the architecture doc.**
  - Update the "Composite handle controls" section to `ActiveObject`, and describe
    `ActPoint`'s `handle_style` (active) vs `style` (content) and the unified
    `set_handles_enabled` / `set_handles_visible` / `set_drag_modifiers`.
- [x] **6.2 — Changelog.**
  - Create `docs/changelog/2026/10/DD_feat-active-object-unification.md` per
    `dev/workflows/changelog.md` (title from `uv run python tools/last-release.py`;
    sections: New Features for `ActiveObject` + unified handle API + point styling,
    Bug Fixes for selection highlight + line drag).
- [x] **6.3 — Changelog index (deferred).**
  - The `docs/changelog/index.md` entry is added at PR time (after the hash rename).

## Validation

`uv run mkdocs build --strict`

## Notes

- Filename uses the actual branch name at implementation time (`/`→`-`); the
  PR-time hash rename happens later (see `dev/workflows/pull-request.md`).
