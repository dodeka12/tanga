# Phase 5 — Integration coverage + full validation gate

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add an integration test for the per-view message and run the full repo gate.

## Files

- Edit: `py/tests/viz/test_layout_api.py` (or a new `py/tests/viz/test_view_visibility.py`)

## Steps

- [x] **5.1 — Two-pane integration test**
  - Build two `SceneView`s of one scene with a fake transport; call
    `left.set_visible("e", False)` and assert exactly one `view_visibility`
    message targeting `left.id` with `hide == ["e"]`, and that the right view
    and its filter are untouched.
- [x] **5.2 — `visible_in` default**
  - Assert `visible_in=None` (default) omits the field from serialization, i.e.
    an entity added without the kwarg still renders in all views.
- [x] **5.3 — Full gate**
  - Run the full Python suite, lint, and type check.

## Validation

`uv run pytest -rs && uv run ruff check . && uv run ty check`
