# Phase 7 — Docs + changelog

## Goal

Document the `CoordinateMapper` seam in the developer docs, regenerate example
docs, and add the branch changelog.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- New: `docs/changelog/2026/09/29_feat-calibrated-labeling.md`
- Regenerate: `docs/py/examples/...` (via `generate-example-docs.py`)

## Steps

- [ ] **7.1 — Developer docs**
  - In `viz-architecture.md` (camera section), add a short paragraph on the
    `CoordinateMapper` protocol + `PlanarMapper`/`CalibratedPlaneMapper` and how
    `LabelMeStore(mapper=…)` uses it.
- [ ] **7.2 — Example docs**
  - `uv run python tools/generate-example-docs.py` (commits the new example page).
- [ ] **7.3 — Changelog**
  - Write `docs/changelog/2026/09/29_feat-calibrated-labeling.md` per
    `dev/workflows/changelog.md`, with a "Breaking" section (loader return types,
    `dumps` formatting).
- [ ] **7.4 — Full validation**
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
