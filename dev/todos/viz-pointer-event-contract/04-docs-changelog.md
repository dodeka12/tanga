# Phase 4 — Docs + changelog

## Goal

Update the developer docs for the unified event fields / pixel frame and append
the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- Edit: `docs/changelog/2026/09/30_feat-calibrated-pane-interaction.md`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Steps

- [x] **4.1 — Update the event hierarchy in `viz-controls-and-interactions.md`**
  - Added `ray_origin`/`ray_direction` to the `ClickEvent` line and documented
    `screen_position` as canvas-local for all pointer events.
- [x] **4.2 — Update the surface paragraph**
  - Noted the frontend sends the picking ray on click/drag_start and the backend
    rebases via `click_anchor`/`drag_anchor` from that ray (no `pixel_ray`).
- [x] **4.3 — Append the changelog**
  - Added a `Bug Fixes` bullet for the click-created point offset.

## Validation

`uv run pytest -q && uv run mkdocs build --strict`

## Notes

- `docs/changelog/index.md` is updated at PR time, not now.
