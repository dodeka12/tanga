# Phase 4 — Docs + changelog

## Goal

Document the plane drag surface in the developer docs and add the branch
changelog.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- Edit: `docs/dev/architecture/viz-architecture.md`
- New: `docs/changelog/2026/09/29_feat-plane-drag-surface.md`

## Steps

- [x] **4.1 — Developer docs**
  - In `viz-controls-and-interactions.md`, note that `ActImagePlane` is now
    mapper-aware (plane from a `CoordinateMapper`, `VIEW_PLANE` drag) and the
    `entity` is pluggable (image vs. transparent hit plane).
- [x] **4.2 — Changelog**
  - Write `docs/changelog/2026/09/29_feat-plane-drag-surface.md` per
    `dev/workflows/changelog.md` (New Features; no breaking change expected).
- [x] **4.3 — Full validation**
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
