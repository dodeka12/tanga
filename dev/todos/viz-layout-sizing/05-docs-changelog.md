# Phase 5 — Docs, example, changelog

## Goal

Document the new sizing model, add a runnable example exercising it, and write
the branch changelog. Then run the full validation gate.

## Files

- Edit: `docs/py/viz/visualizer/split-views.md` (Size units + containers)
- Edit: `docs/py/viz/interaction/control-views.md` (control size floors)
- Edit: `docs/py/viz/app/layouts.md` (a short note + link)
- Edit: `py/examples/viz/dialogs/dialog_demo.py` (or add a new example)
- New: `docs/changelog/YYYY-MM-DD_feat-viz-layout-sizing.md` (per workflow)

## Steps

- [ ] **5.1 — Document the flex mapping.**
  - In `split-views.md`, document `StackView`/`GroupView` `gap`/`align`/`justify`
    and the `preferred_*` → flex table from the README (`fr` = grow, `px`/`%` =
    fixed basis, `None`/`auto` = natural), plus the new `SplitView` fixed-pane
    splitter behavior.

- [ ] **5.2 — Document control floors.**
  - In `control-views.md`, note the `ControlView` default `min_width`/`min_height`
    floors and that `None` disables them; add `gap`/`align`/`justify` to the
    `StackView`/`GroupView` signatures shown there.

- [ ] **5.3 — Example.**
  - Extend `py/examples/viz/dialogs/dialog_demo.py` (or add a sibling example) to
    show: a horizontal `StackView` where a `TextAreaView` uses
    `preferred_width=Size.fr(1)` to fill beside a button, `gap=8`, and a dialog
    shown with `width=Size.px(600)`; update the example docs per
    `dev/workflows/example-docs.md` if a new example file is added.

- [ ] **5.4 — Changelog.**
  - Follow `dev/workflows/changelog.md`: create the branch changelog under
    `docs/changelog/` (title from `uv run python tools/last-release.py`; sections
    `New Features` and `Bug Fixes`), then update `docs/changelog/index.md`.

- [ ] **5.5 — Full validation.**
  - Run the whole Python suite, all JS pure tests, and the docs build (below).

## Validation

```powershell
uv run pytest py/tests/viz/ -q
node --test 'dev/src/js-tests/*.test.mjs'
uv run mkdocs build --strict
```

## Notes

- The changelog filename uses the actual branch name per `changelog.md` (replace
  `/` with `-`); it is renamed to the hash form at PR time.
