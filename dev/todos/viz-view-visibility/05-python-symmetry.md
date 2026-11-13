# Phase 5 — Python symmetry

**Depends on:** 04 | **Status:** Done

## Problems

- `Visualizer.set_control_visible(cid, …)` / `set_control_enabled(cid, …)`
  resolved only controls, so a `GroupView` id silently no-opped even though
  `GroupView.set_visible` / `set_enabled` already existed.
- `ParamsView._build_group` built the nested `GroupView` without forwarding
  `GroupUI.visible` / `GroupUI.enabled`.

## Change

`py/pytanga/viz/_layout.py`

- `set_control_visible` / `set_control_enabled` fall back to `resolve_group`
  when the id is not a control (`GroupView.set_visible` / `set_enabled` push the
  same `control_state` message).  Docstrings updated.

`py/pytanga/viz/views/params_view.py`

- `_build_group` forwards `visible=ui.visible` / `enabled=ui.enabled`
  (defaulting to `True` when the spec leaves them `None`), so
  `GroupUI(visible=False)` hides the nested sub-panel, which the frontend then
  hides as a whole Parameters row.

## Checks

- `uv run pytest py/tests/viz/test_layout_api.py py/tests/viz/test_params_view.py -q`
- `uv run ruff check py/ && uv run ruff format --check py/`
