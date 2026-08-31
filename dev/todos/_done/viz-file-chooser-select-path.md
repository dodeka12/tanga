# pytanga.viz bug report: `FileChooserView` in a `SplitView` layout never shows the selected path

Status: report for upstream (pytanga) filing. No code changes applied in pytanga for this issue;
this is a read-only analysis.

`tanga-py` version: current editable checkout (post-1.11.1, see
`docs/changelog/2026-08-31_3ea3a8ab.md`).

## Use case

An app subclasses `pytanga.viz.VisualizerApp` and shows a `SplitView` layout. One pane contains a
`FileChooserView` (a layout *view* control) whose `on_change` handler loads the selected file:

```python
self._pupils_file = FileChooserView(
    "pupils_file", label="Load pupils CSV", root=str(configs), on_change=self.on_pupils_file
)

async def on_pupils_file(self, path, _event):
    ...  # parses the file and refreshes a TableView
```

When the user clicks **Browse…** and picks a file in the modal browser, the `on_change` handler
fires and the file loads correctly — but the **selected path is not written back into the
`FileChooserView`'s text input**, so the field stays empty.

## Root cause analysis (source inspection)

In `py/pytanga/viz/visualizer.py`, `Visualizer._handle_file_browser_select` (line 2910) stores the
selected path like this:

```python
async def _handle_file_browser_select(self, payload, event):
    cid = payload.get("control_id")
    path = payload.get("path") or ""
    if cid:
        ctrl = self._find_control(cid)      # only panel controls
        if ctrl is not None:
            ctrl.value = path               # never runs for a layout FileChooserView
    handler = self._handler_registry.get(cid)
    if handler is not None:
        await handler(path, event)
```

`Visualizer._find_control` (line 2889) only searches each scene's `_controls` dict — i.e. panel
controls created via `add_file_chooser` / `add_*`:

```python
def _find_control(self, cid):
    for scene in self._scenes.values():
        ctrl = scene._controls.get(cid)
        if ctrl is not None:
            return ctrl
    return None
```

A `FileChooserView` in a `SplitView` layout is a **view** control, not a panel control. It is
registered by `set_layout()` → `_register_control_handlers()` (lines 285 / 299), serialized into the
`view_layout` message, and rendered by the frontend's `createFileChooser`. It is never placed in
`scene._controls`. Consequently:

- `_find_control(cid)` returns `None` for a layout `FileChooserView`.
- `ctrl.value = path` is skipped, so the path is never stored backend-side.
- No `control_update` is pushed, so the frontend text input never shows the selected path.

The `on_change` handler is unaffected: `_register_control_handlers` registers it in
`self._handler_registry` under the view id, so `_handle_file_browser_select` still calls it and the
file loads. Only the path display is broken.

Secondary observation: even for a panel control (`add_file_chooser`), the current code assigns
`ctrl.value = path` directly without pushing a `control_update`, so the input field would not
refresh there either — the value changes backend-side but is never sent to the frontend.

## Expected behaviour

After a file is selected in the modal browser, the `FileChooserView`'s text input should show the
chosen absolute path, and the backend control/view value should match.

## Suggested fix

1. Resolve view controls too — add a `_find_control_view(cid)` that walks the registered layout
   (`self._layouts[name]` via `iter_control_views`) and returns the matching `ControlView` (or
   `None`).
2. In `_handle_file_browser_select`, after resolving the control, update **and push** the value:
   - panel control → `self.set_control_value(cid, path)` (pushes `control_update`), or
   - view control → `self.set_control_view_value(view, path)` (pushes `control_update`).

`set_control_view_value` already handles `FileChooserView` (coerces `value` to `str` and pushes a
`control_update`), so the view-control branch is a one-liner once the view is found.

## Reference source locations (current editable checkout)

- `Visualizer.set_layout` — `py/pytanga/viz/visualizer.py:285`
- `Visualizer._register_control_handlers` — `py/pytanga/viz/visualizer.py:299`
- `Visualizer._find_control` — `py/pytanga/viz/visualizer.py:2889`
- `Visualizer._handle_file_browser_select` — `py/pytanga/viz/visualizer.py:2910`
- `set_control_view_value` / `get_control_view_value` — `py/pytanga/viz/views.py`
- Frontend `FileChooserView` / `createFileChooser` — `py/pytanga/viz/templates/views/file-chooser-view.js`,
  `py/pytanga/viz/templates/controls-panel.js`

## Downstream workaround (not part of this fix)

The `seating-plan` app currently works around this by calling
`viz.set_control_view_value(self._pupils_file, path)` in its own `on_change` handler. That can be
removed once this is fixed upstream.
