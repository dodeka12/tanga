# Phase 5 — Docs + changelog

## Goal

Document the interaction-surface architecture and add the branch changelog.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- Edit: `docs/dev/architecture/viz-architecture.md`
- New: `docs/changelog/2026/09/29_feat-interaction-surface.md`

## Steps

- [ ] **5.1 — Developer docs**
  - Replace the "Image canvas" section's `ActImagePlane` description with the
    pane/surface/visual model; document `SceneView.surface` + `read_only` and the
    per-pane surface pointer events.
- [ ] **5.2 — Changelog**
  - Write `docs/changelog/2026/09/29_feat-interaction-surface.md` (New Features +
    a note that the calibrated drag-to-draw is fixed).
- [ ] **5.3 — Full validation**
  - `uv run pytest -rs`, `uv run ruff check .`, `uv run ty check`,
    `node --test 'js/dev/tests/*.test.mjs'`, `node js/dev/tests/check-syntax.mjs`,
    `uv run mkdocs build --strict`.

## Validation

```
uv run pytest -rs && uv run ruff check . && uv run ty check && uv run mkdocs build --strict
```

## Notes

- Final phase per `dev/workflows/create-plan.md`; PR/hash rename follows
  `dev/workflows/pull-request.md`.
