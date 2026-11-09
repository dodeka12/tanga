# Phase 1 — View tooltip API (Python)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Give control views and groups a runtime `set_tooltip`, make group/menu
serialization always carry `tooltip` (so a cleared tooltip survives a layout
re-push), add `MenuView(tooltip=…)`, and forward `GroupUI(tooltip=…)` into the
nested group built by `ParamsView`.

## Files

- Edit: `py/pytanga/viz/views/control_view.py`
- Edit: `py/pytanga/viz/views/group_view.py`
- Edit: `py/pytanga/viz/views/menu_view.py`
- Edit: `py/pytanga/viz/views/params_view.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_views.py`
- Edit: `py/tests/viz/test_params_view.py`
- Edit: `py/tests/viz/test_layout_api.py`

## Steps

- [x] **1.1 — `ControlView.set_tooltip` (`views/control_view.py`)**
  - Add next to `set_selected`:
    ```python
    def set_tooltip(self, tooltip: str) -> None:
        """Set this control's tooltip text and push ``control_state``."""
        self.tooltip = tooltip
        self.control.tooltip = tooltip
        if self._push_state is not None:
            self._push_state(self.id, {"tooltip": self.tooltip})
    ```
  - Docstring must state that an empty string clears the tooltip and that both
    copies (`self.tooltip`, `self.control.tooltip`) are kept in sync.

- [x] **1.2 — `Visualizer.set_control_tooltip` (`visualizer.py`, `_layout.py`)**
  - `_layout.py`: extract `resolve_control_view(cid) -> ControlView | None` from
    `resolve_control` (same layouts + dialogs walk; `resolve_control` now
    delegates to it), and add `set_control_tooltip(cid, tooltip)` that resolves
    the **view** and calls `view.set_tooltip(tooltip)` (no-op when unresolved).
    The view setter already pushes through its injected `_push_state`.
  - `visualizer.py`: add `set_control_tooltip(control_id, tooltip)` next to
    `set_control_enabled` / `set_control_visible`, delegating to
    `self._layout.set_control_tooltip(...)`.
  - Docstring: works for panel, dialog and banner controls alike (same resolver).

- [x] **1.3 — `GroupView` tooltip (`views/group_view.py`)**
  - Add `set_tooltip(text)` modelled on `set_title` (lines 103-107): assign
    `self.tooltip`, push `{"tooltip": self.tooltip}` through `self._push_state`
    when set. Do **not** push `title` (that would rename the group).
  - `_serialize`: replace the `if self.tooltip:` guard with an unconditional
    `result["tooltip"] = self.tooltip` (empty string = cleared), so a re-push
    clears the header tooltip.

- [x] **1.4 — `MenuView(tooltip=…)` (`views/menu_view.py`)**
  - Add a keyword-only `tooltip: str = ""` parameter, store `self.tooltip`, and
    emit `result["tooltip"] = self.tooltip` in `_serialize` (always).

- [x] **1.5 — `ParamsView._build_group` passthrough (`views/params_view.py`)**
  - `GroupView(title=title, children=[nested], collapsed=ui.collapsed,
    tooltip=ui.tooltip or "")`.

- [x] **1.6 — Tests**
  - `test_views.py`: replace `test_serialize_tooltip_omitted_when_empty` with
    `test_serialize_tooltip_empty_by_default` (`node["tooltip"] == ""`); add
    `MenuView(tooltip="…")` serialization; add `GroupView.set_tooltip` and
    `ControlView.set_tooltip` push tests using a stub `_push_state` (mirror the
    existing `set_title` / `set_enabled` tests).
  - `test_params_view.py`: a `GroupUI(tooltip=…)` field reaches the nested
    `GroupView.tooltip` (and the serialized node).
  - `test_layout_api.py`: `viz.set_control_tooltip("radius", "Radius in mm")`
    mutates `view.tooltip`/`view.control.tooltip` and pushes
    `{"type": "control_state", "id": "radius", "tooltip": "Radius in mm"}`
    using the existing `_mount` helper; unknown id does not push.

## Validation

```bash
uv run pytest py/tests/viz/test_views.py py/tests/viz/test_params_view.py py/tests/viz/test_layout_api.py -q
```

## Notes

- `ControlView._serialize` already always emits `tooltip`, which is why controls
  update correctly on a re-push while groups did not — this phase closes that
  asymmetry.
- The tooltip is **not** re-sent as part of `view_layout` changes; the setter
  path uses the granular `control_state` message.
