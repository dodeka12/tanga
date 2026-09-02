# Banners & Dialogs

Banners are transient overlays shown over the viewer — informative messages,
acknowledge prompts, option selectors, and yes/no/cancel dialogs.  They are
removable from the backend and support markdown/KaTeX text.

## Banner kinds

| API | Use |
|-----|-----|
| `viz.alert(text, *, on_ok=…)` | Single "OK" acknowledge banner |
| `viz.show_banner(text, *, controls=[…])` | Custom options (any control: `Button`/`Slider`/`Dropdown`) |
| `viz.confirm(text, *, on_yes=…, on_no=…, on_cancel=…)` | Yes / No / Cancel |
| `viz.show_banner(..., dismissable=False)` | Modal banner (dimmed backdrop, no close) |

```python
viz.alert("## Done\n\nThe computation finished.", title="Notice")
viz.confirm("Proceed?", on_yes=self.on_yes, on_no=self.on_no)
bid = viz.show_banner(
    "## Busy…\n\nPlease wait.",
    title="Working",
    dismissable=False,       # modal — blocks the scene, cannot be clicked away
)
```

## Alignment

`align_x` / `align_y` (both in `[0, 1]`) pin the banner to its container:

- `(0, 0)` — the banner's **top-left** corner at the container's top-left;
- `(1, 1)` — the banner's **bottom-right** corner at the container's bottom-right;
- `(0.5, 0.5)` — centered.

For **global** banners the container is the viewport; for **per-scene** banners
it is the scene pane.

## Global vs per-scene

- `scene_name=None` (default) → **global**, full-screen.
- `scene_name="<name>"` → **per-scene**, shown in every pane displaying that
  scene (`""` is the main scene).  `VizSceneHandle` exposes the same API
  scoped to its scene — `show_banner`, `alert`, `confirm`, `remove_banner`,
  and `clear_banners` (plus their `*_async` forms) — without the `scene_name`
  argument:

```python
viz.show_banner("Global")
detail = viz.scene("detail")
detail.show_banner("Only over the detail scene")
detail.alert("Detail-specific notice")
detail.confirm("Rebuild the detail scene?")
```

## Auto-hide and removal

- `auto_hide=True` (default) — the frontend removes the banner as soon as the
  user selects an option.
- `auto_hide=False` — the backend must remove it explicitly:

```python
bid = viz.show_banner("Please wait…", dismissable=False, auto_hide=False)
# … later …
viz.remove_banner(bid)     # or viz.clear_banners()
```

## Running work from a handler

Control handlers run on the server's event loop, so a long synchronous
computation would freeze the scene.  Show a banner, **await** its push so it is
visible, then fire-and-forget the computation onto the user loop with a
one-shot `done` callback that cleans up:

```python
async def on_release(self, value, event):
    bid = await self.viz.show_banner_async("## Calculating…", dismissable=False)

    async def _work():
        await asyncio.to_thread(time.sleep, 3)   # simulate blocking compute
        return value

    def _done(result):
        self.viz.update_entity("ent", Sphere(Point(0, 0, 0), radius=result))
        self.viz.remove_banner(bid)
        self.viz.flush()

    self.submit_user(_work, done=_done)
```

For plain synchronous scripts (no `VisualizerApp`), use
`await self.viz.run_blocking(fn)` instead of `submit_user`.

## Dialogs

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
| `align_x` / `align_y` | `float` | `0.5` | Anchor in `[0, 1]` (see [Alignment](#alignment)) |
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

- `py/examples/viz/banners/banner_types.py` — every banner kind.
- `py/examples/viz/banners/heavy_work.py` — a slider that triggers a 3 s
  computation on release.
- `py/examples/viz/dialogs/dialog_demo.py` — a dialog with view content, a
  menu-bar reopen, and a modal variant.

## See Also

- [Controls](../interaction/controls.md) — `add_slider`/`add_dropdown`/`add_button`/`add_control_group`
- [Handlers & Lifecycle](handlers.md) — the handler contract and the app lifecycle
