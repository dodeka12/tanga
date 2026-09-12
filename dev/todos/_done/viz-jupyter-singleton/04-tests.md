# Phase 4 — Regression & integration tests

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`) for the
> subsystem(s) this work touches, so the new code aligns with the documented
> architecture.  If this work introduces or changes architecture, update the
> developer docs.

## Goal

Confirm the singleton + reset semantics do not regress the existing viz suite
(~313 independent constructions, `VisualizerApp`, display/context-manager
behaviour).

## Files

- Edit: `py/tests/viz/test_visualizer_singleton.py` (any gaps)

## Steps

- [x] **4.1 — Cover edge cases in the singleton test file**
  - `reset()` yields a fresh instance after a singleton was created.
  - The non-Jupyter path constructs independent instances with different configs
    (distinct `title`/`camera`/`space_dim`).
  - The context managers (`with viz:` / `with viz.scene(name):`) still clear +
    show + flush; the existing `test_display.py::TestContextManager` must pass
    unchanged.

- [x] **4.2 — Run the full viz suite + lint**
  - `uv run pytest py/tests/viz -q` — all green.
  - `uv run ruff check py/pytanga/viz/ py/tests/viz/` — clean.

## Validation

`uv run pytest py/tests/viz -q && uv run ruff check py/pytanga/viz/ py/tests/viz/`

## Notes

- Under pytest `_is_jupyter()` is `False`, so the singleton is inert in the
  existing suite; this phase is a regression guard, not a rewrite.
- `uv run pytest py/tests/viz -q` is fully green (1432 passed, 2 skipped).
  `ruff check` passes on the files touched here (`visualizer.py`,
  `test_visualizer_singleton.py`).  The aggregate `ruff check py/pytanga/viz/
  py/tests/viz/` still reports 6 **pre-existing** F401/F841 errors in unrelated
  files (`test_active.py`, `test_entry_points.py`, `test_viz_2d.py`,
  `test_viz_styles.py`, `sdf/test_sdf_object_serialization.py`,
  `sdf/test_ecompose_operators.py`); they are out of scope for this plan and
  left untouched.
