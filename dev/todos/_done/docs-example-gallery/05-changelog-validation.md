# Phase 5 — Changelog + full validation

## Goal

Record the change and run the full gate.

## Steps

- [x] **5.1 — Changelog**
  - Create/append the branch changelog per `dev/workflows/changelog.md` (New
    Features bullet for the searchable, per-example docs gallery).

- [x] **5.2 — Full validation**
  - `uv run mkdocs build --strict` (docs gate).
  - `uv run ruff check` on touched Python (`tools/`, `docs/_hooks/`).
  - `uv run pytest -q` (full suite).
  - Spot-check search for a few sample keywords (e.g. `timeline`, `PGA3`,
    `banner`) in the built site.

## Validation

```
uv run mkdocs build --strict && uv run ruff check tools/ docs/_hooks/ && uv run pytest -q
```
