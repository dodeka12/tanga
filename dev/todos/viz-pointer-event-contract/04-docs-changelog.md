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

- [ ] **4.1 — Update the event hierarchy in `viz-controls-and-interactions.md`**
  - Add `ray_origin`/`ray_direction` to the `ClickEvent` line and note that
    `screen_position` is canvas-local for all pointer events.
- [ ] **4.2 — Update the surface paragraph**
  - Clarify that the frontend sends the picking ray on click/drag_start and the
    backend rebases via `click_anchor`/`drag_anchor` using that ray (no
    `pixel_ray` reconstruction).
- [ ] **4.3 — Append the changelog**
  - Add a `Bug Fixes` bullet: click-created points now resolve their anchor from
    the frontend's picking ray in a common canvas-local pixel frame (fixes the
    point appearing offset from the cursor).

## Validation

`uv run pytest -q && uv run mkdocs build --strict`

## Notes

- `docs/changelog/index.md` is updated at PR time, not now.
