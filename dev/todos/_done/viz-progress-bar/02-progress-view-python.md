# Phase 2 — ProgressBarView (Python) + exports

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add `ProgressBarView(ControlView[ProgressBar])`, export it publicly, wire
`control_to_view`, and test the view's push path.

## Files

- Edit: `py/pytanga/viz/views/control_views.py`
- Edit: `py/pytanga/viz/views/__init__.py`
- Edit: `py/pytanga/viz/__init__.py`
- Edit: `py/pytanga/viz/views/functions.py`
- Edit: `py/tests/viz/test_progress_bar.py`

## Steps

- [x] **2.1 — `ProgressBarView` (`control_views.py`)**
  - `_node_type = "progress_bar_view"`; constructor `(cid, *, title="",
    value=0.0, total=0, indeterminate=False, text="", tooltip="", <size specs>)`;
    build `self.control = ProgressBar(...)`.
  - Convenience push methods: `set_text`, `set_total`,
    `set_indeterminate(on=True)`, `set_progress(value, text=None)`, `start()`,
    `stop()`, `reset()`; each mutates `self.control` and calls `_push_value()`
    (pushes `self.control.get_value()`).
  - Default sizes: `preferred_width=Size.px(220)`, `min_width=Size.px(160)`,
    `min_height=Size.px(40)`.

- [x] **2.2 — Exports (`views/__init__.py`, `viz/__init__.py`)**
  - Add `ProgressBarView` (views) and `ProgressBar` + `ProgressBarView` (viz) to
    imports and `__all__` (alphabetical position).

- [x] **2.3 — `control_to_view` (`functions.py`)**
  - Import `ProgressBar`/`ProgressBarView` and add a branch returning a
    `ProgressBarView` that reuses the control (mirrors the other branches).

- [x] **2.4 — Tests (`test_progress_bar.py`)**
  - `_serialize()` has `type == "progress_bar_view"` and the five fields.
  - `set_text`/`set_total`/`set_indeterminate`/`set_progress`/`reset` push the
    expected dict via a stub `_push`.
  - Inherited `set_value(number)` pushes the full dict; `control_to_view` wraps a
    `ProgressBar` into a `ProgressBarView`.

## Validation

```bash
uv run pytest py/tests/viz/test_progress_bar.py py/tests/viz/test_views.py py/tests/viz/test_layout_api.py -q
```
