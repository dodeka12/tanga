# Phase 2 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md`.  This phase updates the
> documented surface behavior that Phase 1 changed.

## Goal

Document the new nearest→furthest, trigger-aware hit-arbitration and record the
change in the existing branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- Edit: `py/pytanga/viz/_surface.py` (module docstring)
- Edit: `docs/changelog/2026/10/15_feat-bg-image-shader.md` (append)

## Steps

- [x] **2.1 — Developer docs (`viz-controls-and-interactions.md`).**
  - In the "Interaction surface" section (currently "the frontend emits
    `interaction:drag_*`/`click` events for the pane's *empty space*"), update it
    to: the surface is the furthest hit candidate; a gesture goes to the nearest
    hit object whose `interaction.triggers` match (event type + button +
    modifiers), falling through to the surface when nearer entities decline.

- [x] **2.2 — `_surface.py` docstring.**
  - Replace the "pointer hits *empty space*" wording with: the frontend emits its
    drag/click events when the pointer hits empty space **or** when nearer
    entities do not register a matching trigger.

- [x] **2.3 — Changelog.**
  - Append a `## Bug Fixes` bullet to the existing branch changelog
    `docs/changelog/2026/10/15_feat-bg-image-shader.md` (do not create a new
    file): pointer gestures now fall through to the pane surface when nearer
    entities do not register the gesture (fixes ctrl+drag brightness/contrast over
    a label entity).

- [x] **2.4 — Build.**
  - `uv run mkdocs build --strict`.

## Validation

`uv run mkdocs build --strict`

## Notes

- Changelog naming/renaming (branch name → squashed-hash) is finalised at PR time
  per `dev/workflows/pull-request.md`; this phase only appends to the branch file.
