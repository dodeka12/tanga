# Phase 5 — Tests, docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Lock in the `Protocol`-based behavior with tests, correct a stale
`__getattr__` reference in the developer docs, and add the changelog.

## Files

- Edit: `py/tests/viz/test_views.py`
- Edit: `docs/dev/architecture/viz-architecture.md`
- New: `docs/changelog/2026/10/DD_fix-viz-control-refactor.md` (append)

## Steps

- [x] **5.1 — tests (`test_views.py`)**
  - Add a `ToolbarView` test asserting a variant-carrying child is forced to
    `TOOLBAR` and a non-variant child (e.g. `LabelView`) is left untouched
    (mirror `TestMenuView.test_override_variant_*`).
  - Add (or extend) a test that the `functions.py` iterators still traverse
    `children`/`overlay` correctly through a `SceneView(overlay=[…])` +
    `StackView([…])` tree (no regression from the `Protocol` rewrite).

- [x] **5.2 — architecture docs**
  - `docs/dev/architecture/viz-architecture.md`: fix the stale
    "`ControlView.__getattr__` forwards reads and `set_value`/`undo`/`redo` to
    the control" sentence in the "Adding a new control kind" recipe (≈ line 165)
    to say the views expose explicit typed forwarders.  (This is a leftover from
    the earlier `__getattr__` removal.)
  - Confirm no other `docs/dev/` file documents `getattr`/`hasattr` for the
    variant-forcing or tree-walk we changed; if one does, update it.

- [x] **5.3 — changelog**
  - Append a `## Refactor` bullet to
    `docs/changelog/2026/10/DD_fix-viz-control-refactor.md` per
    `dev/workflows/changelog.md` (describe replacing `getattr`/`hasattr`
    duck-typing with runtime-checkable `Protocol`s in the viz tree).

## Validation

```bash
uv run pytest py/tests/viz -q && uv run ty check && uv run ruff check . && uv run mkdocs build --strict
```

## Notes

- Finalize the changelog filename to the hash form at PR time per
  `dev/workflows/pull-request.md`.
- The stale `viz-architecture.md` `__getattr__` sentence is unrelated to this
  work's runtime behavior but is now factually wrong; correcting it is
  in-scope for the docs phase.
