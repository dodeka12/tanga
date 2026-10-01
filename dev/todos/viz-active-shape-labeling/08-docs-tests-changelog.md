# Phase 8 — Docs, developer-docs update, tests, changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If this
> work introduces or changes architecture, update the developer docs (this phase
> does).

## Goal

Document the new act elements and the keyboard facility, update the developer
architecture docs (the keyboard facility extends the interaction contract),
finalize tests, and write the branch changelog.

## Files

- New: `docs/py/viz/entities/active-elements/act-ellipse.md`
- New: `docs/py/viz/entities/active-elements/act-polygon.md`
- Edit: `docs/py/viz/entities/active-elements/index.md`
- Edit: `docs/py/viz/entities/active-elements/act-rectangle2d.md` (document `on_click`)
- Edit: `docs/py/viz/interaction/object-interaction.md` (document `on_key` / keyboard)
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md` (document the keyboard facility)
- New: `docs/changelog/2026/09/28_feat-more-act-entities.md`
- Edit: tests as needed (finalize `test_act_ellipse.py`, `test_act_polygon.py`, `test_keyboard.py`, `test_active.py`, `test_act_rectangle2d.py`)

## Steps

- [x] **8.1 — Active-elements docs.** Write `act-ellipse.md` and `act-polygon.md`
  (Quick Start, constructor, properties, handlers), add them to `index.md`, and
  note `on_click` in `act-rectangle2d.md`.
- [x] **8.2 — Interaction docs.** Document `on_key`/`KeyEvent`/`KeyBinding` and the
  per-pane keyboard model in `object-interaction.md`.
- [x] **8.3 — Developer docs.** Update
  `docs/dev/architecture/viz-controls-and-interactions.md` to record the keyboard
  facility: `SceneConfig.keyboard`, the `interaction:key` message, and the
  `(key:{scene}:{key}, "key")` registry key.  Update `viz-architecture.md` only if
  the ownership table changes.
- [x] **8.4 — Tests finalize.** Run the full viz suite; fill any coverage gaps for
  the new composites/bindings/keyboard.
- [x] **8.5 — Example docs.** Run `tools/generate-example-docs.py` (and `--check`).
- [x] **8.6 — Changelog.** Add `docs/changelog/2026/09/28_feat-more-act-entities.md`
  per `dev/workflows/changelog.md` (run `uv run python tools/last-release.py` for
  the title).  Leave the index update + hash rename to PR time
  (`dev/workflows/pull-request.md`).

## Validation

```
uv run pytest -q
uv run python tools/generate-example-docs.py --check
uv run mkdocs build --strict
```

## Notes

- The keyboard facility is a new documented contract — do not merge without the
  `viz-controls-and-interactions.md` update in 8.3.
- Changelog filename replaces `/` with `-`; final hash rename happens at PR time.
