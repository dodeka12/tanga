# Phase 6 — docs + changelog

## Goal

Document the new public API and record the changes in the branch changelog per
the repo workflow.

## Files

- Edit: `docs/py/viz/sdf/sdf-objects.md` (smooth CSG + `Transform.from_operator`)
- Edit: `docs/py/expression/…` (if an expression docs page exists — otherwise
  skip; verify before editing)
- New: `docs/changelog/2026-09-04_feat-view-architecture.md` (append to the
  existing branch changelog if one exists for this branch)

## Steps

- [x] **6.1 — Document smooth CSG**
  - In `docs/py/viz/sdf/sdf-objects.md`, extend the `ECompose` operator table
    and the `Composed`/`SdfGroup` sections with the three smooth modes and the
    `(obj, mode, smoothness)` / `SdfStyle(smoothness=...)` forms, noting the
    frontend default `0.1` and the rounded-join semantics.

- [x] **6.2 — Document `Transform.from_operator`**
  - In the `viz` docs (wherever `VizGroup`/scene-graph transforms are
    documented), add `Transform.from_operator(...)` and note that `Transform` is
    now importable from `pytanga.viz`.

- [x] **6.3 — Branch changelog**
  - Follow `dev/workflows/changelog.md`. If
    `docs/changelog/2026-09-03_feat-view-architecture.md` already exists, append
    to it; otherwise create `docs/changelog/YYYY-MM-DD_feat-view-architecture.md`
    (use the current date).
  - Title `# Changes since version 1.17.0` (confirm with
    `uv run python tools/last-release.py`).
  - Add bullets: `Expression.bind()`/`evaluate()` (+ `AffineExpression`);
    reflected `MV ^ Variable`/`MV | Variable`; `Transform.from_operator()` +
    `Transform` export; smooth SDF CSG modes + `smoothness`.

- [x] **6.4 — Validate**
  - Re-run the full suite and lint.

## Validation

`uv run pytest -q && uv run ruff check py/`

## Notes

- The `docs/changelog/index.md` entry and the hash rename happen at PR time (see
  `dev/workflows/pull-request.md`), not in this phase.
- Only edit an expression docs page if one actually exists; do not create a new
  docs structure just for this change.
