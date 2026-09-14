# Dialogs

A `Dialog` is a titled overlay whose body holds arbitrary view content (any
`View`, e.g. a `StackView` of control views).  It is a sibling of the banner —
removable from the backend, draggable by its title bar (clamped to the
viewport), resizable from its bottom-right corner, and closable by a ✕ unless
modal:

```python
viz.show_dialog(
    StackView("vertical", [
        SliderView("gain", label="Gain", min=0.0, max=2.0, value=1.0),
        ButtonView("apply", label="Apply"),
    ]),
    title="Settings",
    on_close=self.on_dialog_closed,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | `View` | *(required)* | The dialog body (any view; control handlers are registered automatically) |
| `id` | `str` | auto | Dialog id (returned by `show_dialog`) |
| `title` | `str` | `""` | Title-bar text |
| `align_x` / `align_y` | `float` | `0.5` | Anchor in `[0, 1]` (see [Alignment](banners.md#alignment)) |
| `dismissable` | `bool` | `True` | `False` = modal (dimmed backdrop, no ✕) |
| `on_close` | `Callable` | `None` | Async callback fired when the dialog closes |
| `width` | `SizeSpec` | `None` | Explicit dialog width (`Size.px` / `Size.percent`); `None` shrink-wraps |
| `height` | `SizeSpec` | `None` | Explicit dialog height; `None` shrink-wraps |
| `scene_name` | `str` | `None` | `None` = global; `"<name>"` = per-scene (every pane of that scene) |

`FileChooserDialog` (see [File Chooser](file-chooser.md)) is a full file-open
dialog (a listing + path line + OK/Cancel) you pass to `show_dialog`.

Remove with `viz.remove_dialog(id)` or `viz.clear_dialogs()`.  `VizSceneHandle`
exposes `show_dialog` / `remove_dialog` / `clear_dialogs` scoped to its scene
(plus `*_async` forms), mirroring the banner API.

## Examples

- `py/examples/viz/ui/dialogs/dialog_demo.py` — a dialog with view content, a
  menu-bar reopen, and a modal variant.
- `py/examples/viz/ui/dialogs/file_chooser_dialog.py` — a `FileChooserView`
  embedded in a layout and wrapped as a `FileChooserDialog`.

## See Also

- [Banners](banners.md) — `alert`/`confirm`/`show_banner` and alignment semantics
- [File Chooser](file-chooser.md) — `FileChooserView` / `FileChooserDialog`
