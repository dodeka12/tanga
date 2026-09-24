# Runtime Updates — layouts, images & background

This page collects the patterns for changing what the viewer shows **after it
is already running**, without rebuilding the whole UI.  The common thread: the
viewer keeps every live view keyed by its stable `id`, so **reuse the same
Python object** to update a view in place, and use the granular `set_*` /
`set_view_*` APIs for single-value changes (rather than re-pushing the layout).

## Updating a layout (reuse the view objects)

`set_layout` re-serializes and re-pushes the whole `view_layout` tree, but the
frontend **reconciles it by view id** instead of rebuilding it: a `SceneView`
whose Python object is reused keeps its WebGL scene/camera, and only views that
were added or removed are created or torn down.

Keep the panes (and any control you want to preserve) as persistent variables,
then re-push the same `View` objects:

```python
from pytanga.viz import CameraView, SceneView, SplitView, Visualizer

left = SceneView("world", camera_view=CameraView(cam, navigation="2d", ...))
right = SceneView("world")
body = SplitView("horizontal", [left, right])
layout = SplitView("vertical", [toolbar, body])   # toolbar above the two panes


def swap_panes() -> None:
    body.children.reverse()      # reorder the *same* pane objects
    viz.set_layout(layout)       # reconcile: panes re-attach, nothing is rebuilt
```

- **Reuse = keep.** The same `SceneView` object → the same `id` → the frontend
  re-attaches its live view (the WebGL context survives).
- **New = rebuild.** A freshly constructed `SceneView` gets a new `id` → the old
  frontend pane is torn down and a new one created.

For a single pane, prefer the per-pane runtime APIs over re-pushing the whole
layout: `viz.set_view_camera(view, camera)` re-aims one pane and
`viz.set_viewport(view, zoom=..., pan=...)` moves its 2D viewport (see
[Split Views](split-views.md)).

## Updating a pane's background image

Swap a pane's `CameraView.background_image` at runtime with
`Visualizer.set_background_image(view, image)`.  It streams the new pixel bytes
and updates **only that pane** — no layout re-push, so every other pane is
untouched:

```python
import numpy as np
from pytanga.viz import ImageData, Visualizer

async def on_open(_value, _event) -> None:
    data = np.random.default_rng().integers(0, 256, size=(480, 640, 3), dtype=np.uint8)
    viz.set_background_image(left, ImageData("camera", data=data))
```

- `view` is the `SceneView` pane (it must be part of a registered layout).
- `image` is an `ImageData` (numpy pixels or a URL — see
  [Image Canvas](../image/image-canvas.md)); pass `None` to clear the background.
- Reuse a fixed image `id` to stream frames without accumulating state.

A streaming example is
`py/examples/viz/camera/pinhole_calibrated_streaming.py`.

## Updating an image view (image canvas)

For a dedicated 2D image pane, `ImageCanvas.set_image(image)` replaces the image
in place — the pixels travel as one binary frame, so there is no full
scene/layout rebuild:

```python
from pytanga.viz import ImageCanvas, ImageData, Visualizer

canvas = ImageCanvas(viz)
canvas.set_image(ImageData("gradient", data=...))   # replace layer 0, re-frame
canvas.add_image(ImageData("mask", data=...))       # append another layer (max 4)
canvas.set_uniform("u_brightness", 0.5)             # shader uniform (JSON only)
```

See [Image Canvas](../image/image-canvas.md) for the full API (`set_image`,
`add_image`, `set_uniform`, overlays, and `scene_view()` for embedding the
canvas in a `SplitView`).

## Updating control state (enable / disable / hide)

A control's `enabled`/`visible` state can be changed at runtime without
re-pushing the layout — the viewer patches just that control in the DOM:

```python
# hide/show a control (e.g. a slider that only makes sense when an entity is visible)
viz.set_control_visible("radius", False)

# disable/enable a control (greyed out, but still rendered)
viz.set_control_enabled("radius", False)
```

Or call the methods on the `ControlView` itself (they push the same message):

```python
radius.set_visible(False)     # same as radius.hide()
radius.set_enabled(False)     # same as radius.disable()
```

The control id is the one you passed when constructing the view.  This reuses
the granular `control_state` message — no `view_layout` re-push, so the rest of
the UI (and any WebGL panes) are untouched.
