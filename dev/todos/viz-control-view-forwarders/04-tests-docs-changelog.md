# Phase 4 — Tests, docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Lock in the explicit-forwarder behavior with tests, update the developer docs
(which currently document `__getattr__` forwarding), and add the changelog.

## Files

- Edit: `py/tests/viz/test_views.py`
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- New: `docs/changelog/2026/10/DD_fix-small-bugs.md`

## Steps

- [ ] **4.1 — tests (`test_views.py`)**
  - Add a test that a `SliderView` exposes `min`/`max`/`step`/`value`/`variant`
    as typed properties (no `__getattr__`), that `dir(view)` lists them, and
    that an unknown attribute raises `AttributeError` (not silently `None`).
  - Add a `menu_view` `_apply_menu_variant` test if not already covered.

- [ ] **4.2 — architecture docs**
  - `viz-controls-and-interactions.md`: in the "Adding a new control kind"
    recipe (currently documents `ControlView.__getattr__` forwarding), replace
    with "explicit typed forwarders on the `*View`" guidance.

- [ ] **4.3 — changelog**
  - Append a `## Refactor` bullet to `docs/changelog/2026/10/DD_fix-small-bugs.md`
    per `dev/workflows/changelog.md`.

## Validation

```bash
uv run pytest py/tests/viz -q && uv run ty check && uv run ruff check . && uv run mkdocs build --strict
```

## Notes

- Finalize the changelog filename to the hash form at PR time per
  `dev/workflows/pull-request.md`.
