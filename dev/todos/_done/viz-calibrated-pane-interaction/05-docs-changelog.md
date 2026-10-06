# Phase 5 — Docs + changelog

## Goal

Document the gesture-arbitration seam and calibrated-pane behaviour, and add the
branch changelog.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- New: `docs/changelog/2026/09/30_feat-calibrated-pane-interaction.md`

## Steps

- [ ] **5.1 — Docs**
  - Document the per-pane "interaction armed/active → navigation yields" seam and
    the calibrated pane's interaction/rendering model.
- [ ] **5.2 — Changelog**
  - Write the branch changelog (Bug Fixes + a note on the calibrated drag-to-draw
    and screen-space markers).
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
