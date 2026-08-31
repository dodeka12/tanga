# pytanga.viz bug report: `controls_define` wipes the control registry, so layout view controls ignore `control_update`

Status: report for upstream (pytanga) filing. No code changes applied in pytanga for this issue;
this is a read-only analysis.

`tanga-py` version: current editable checkout (post-1.11.1).

## Symptom

In a `SplitView` layout, a `TableView` (and a `FileChooserView`) never update when the backend
calls `set_control_view_value(...)`. The backend side is confirmed working — the handler fires, the
`TableView.rows` are updated, and a `control_update` message is pushed — but the browser grid/path
field stay empty.

## Observed behaviour (backend logs)

Instrumenting the downstream app's `on_pupils_file` handler and `_sync_pupils_table` confirms the
backend path is fully working — yet nothing appears in the browser:

```
[DEBUG] on_pupils_file CALLED, path='/home/christian/code/github/dodeka12/seating-plan/_configs/demo_pupils.csv'
[DEBUG] on_pupils_file parsed 25 pupils
[DEBUG] _sync_pupils_table: syncing 25 rows to TableView
[DEBUG] _sync_pupils_table: done; table now has 25 rows
[DEBUG] _sync_pupils_table: syncing 26 rows to TableView
[DEBUG] _sync_pupils_table: done; table now has 26 rows
```

So the `on_change` handler fires, 25 pupils are parsed, and `set_control_view_value` updates the
`TableView` to 25 rows (then 26 after adding a row) — but the rendered Tabulator grid and the
`FileChooserView` path field stay empty. The only remaining link is the frontend `control_update`
application, which is where the bug lives.

## Root cause analysis

The frontend keeps a single module-level `_controlRegistry` (in
`py/pytanga/viz/templates/controls-panel.js`) keyed by control id, where each entry has an
`apply(value)` used by `applyControlValue(id, value)` to push a server-driven value into the DOM.

Two code paths populate that same registry:

1. **Panel controls** — `handleControlsDefine(msg)` renders `add_slider`/`add_button`/… controls
   and, on every `controls_define` / `controls_clear` message, calls `_destroyAll()`, which does:

   ```js
   function _destroyAll() {
       ...
       _controlRegistry = {};   // ← clears EVERYTHING, including layout view controls
       ...
   }
   ```

2. **Layout view controls** — `_buildLayout()` → `buildViewTree()` mounts the `TableView` /
   `FileChooserView` views; each `ControlView._onMounted()` calls `render()`, which calls
   `createTable()` / `createFileChooser()` and registers an entry in the **same** `_controlRegistry`.

The server, on every browser connect, sends — in this order — the `view_layout` message and then a
`controls_define` message for each scene (even when there are zero panel controls; see
`Visualizer._push_controls_async`, wired as the server's `push_controls` callback, and the per-scene
`_push_controls_cb` loop in `VizServer`'s `ready` handler).

Result: `view_layout` registers the table/file-chooser `apply` entries, and the immediately
following `controls_define` runs `handleControlsDefine` → `_destroyAll()` → `_controlRegistry = {}`,
**wiping the layout view controls' entries**. Later `control_update` messages hit
`applyControlValue(id, value)`, find no registry entry, and are silently dropped — so the
`TableView` grid and the `FileChooserView` path field never update.

This affects every layout view control (`TableView`, `FileChooserView`, `TextFieldView`,
`SliderView`, …) that is updated via `set_control_view_value`, not just this app.

## Expected behaviour

`set_control_view_value` on a layout view control updates that control in place; a later
`controls_define`/`controls_clear` (which only concerns panel controls) must not affect layout view
controls.

## Suggested fix

Keep panel controls and layout view controls in separate registries:

- Add a second module-level registry (e.g. `_viewControlRegistry`) that `createTable`,
  `createFileChooser`, and the other `createX` functions write to when called from a view's
  `render()` (i.e. the layout builder), while `handleControlsDefine` keeps using `_controlRegistry`.
- Make `applyControlValue(id, value)` look up both registries (panel first, then view).
- Leave `_destroyAll()` clearing only `_controlRegistry` (the panel one).

Alternatively (smaller change), tag each registry entry with a scope and make `_destroyAll()` clear
only panel-scope entries.

## Reference source locations (current editable checkout)

- `handleControlsDefine`, `_destroyAll`, `applyControlValue`, `createTable`, `createFileChooser` —
  `py/pytanga/viz/templates/controls-panel.js`
- `_buildLayout`, `buildViewTree` — `py/pytanga/viz/templates/viewer.js`,
  `py/pytanga/viz/templates/views/build.js`
- `ControlView._onMounted` / `View.mount` — `py/pytanga/viz/templates/views/control-view.js`,
  `py/pytanga/viz/templates/views/view.js`
- `controls_define` routing to the per-scene view — `py/pytanga/viz/templates/viewer.js` (~line 612),
  `py/pytanga/viz/templates/views/three-view.js` (~line 477)
- `Visualizer._push_controls_async` (always pushes `controls_define`) — `py/pytanga/viz/visualizer.py:3380`;
  per-scene `_push_controls_cb` call in the `ready` handler — `py/pytanga/viz/server.py:817`

## Related

`dev/todos/viz-file-chooser-select-path.md` documents the separate backend gap (`_find_control` only
searches panel controls, so `_handle_file_browser_select` never stores the path for a layout
`FileChooserView`). Even after that is fixed, this registry-reset bug still prevents the path from
being displayed and the table from updating.
