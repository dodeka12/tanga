# Phase 9 — Integration, examples, docs, changelog

## Goal

End-to-end examples (conic/quadric construction + analysis + ray/mesh rendering),
docs, changelog, and full regression.

## Files

- New: `py/examples/ga/quadric/conic_demo.py` (or `py/examples/viz/…`)
- New: `py/examples/ga/quadric/quadric3d_raycast.py`
- Modify: docs pages (via `tools/generate-example-docs.py`)
- New: `docs/changelog/YYYY-MM-DD_<branch>.md` (+ `docs/changelog/index.md`)

## Steps

- [x] **9.1 — examples** — one 2D conic example (embed 5 points → conic → refine →
  draw) and one 3D quadric example (9 points → quadric → `Quadric3D` ray render +
  refine to `Ellipsoid` for mesh/SDF). Add the required docstring header
  (`dev/workflows/example-docs.md`: description + `Run with:` + `Keywords:`).

- [x] **9.2 — docs** — `uv run python tools/generate-example-docs.py` then
  `--check`; `uv run mkdocs build --strict`.

- [x] **9.3 — changelog** — branch changelog per `dev/workflows/changelog.md`.

- [x] **9.4 — full regression** — `uv run pytest` (all suites) + `uv run ruff check`
  and `uv run ruff format --check`.

- [x] **9.5 — Validate** — `uv run pytest` passes; `uv run mkdocs build --strict`
  passes.

## Validation

`uv run pytest && uv run mkdocs build --strict`

## Notes

- Follow `dev/workflows/pull-request.md` (changelog rename, PR summary) when opening
  the PR.
