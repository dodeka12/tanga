# Image Canvas

`ImageCanvas` is the user-facing helper for displaying images — analogous to
`CoordinateSystem`, but for a 2D pixel frame.  It owns a dedicated 2D scene with
a **y-down** pixel frame where **1 unit = 1 pixel**, an `ImageView` (plane +
textures + shader/uniform state), an interactive image plane, and an overlay
group for drawing in pixel coordinates.

## Creating a canvas

```python
from pytanga.viz import ImageCanvas, Visualizer

viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
canvas = ImageCanvas(viz)
```

`ImageCanvas` accepts a `Visualizer` (or a `VizSceneHandle`).  Constructor
keyword arguments:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image_id` | `str` | auto | Id of the underlying `ImageView` entity |
| `stretch` | `StretchMode` | `"fit"` | How the image fills its view |
| `border_px` | `float` | `0.0` | Extra border (px) in the camera framing |
| `on_drag` / `on_drag_start` / `on_drag_end` | `Callable` | `None` | Async drag handlers — see [Interaction](interaction.md) |
| `on_click` | `Callable` | `None` | Async click handler |
| `drag_handlers` | `list[DragBinding]` | `None` | Button+modifier drag bindings |
| `click_handlers` | `list[ClickBinding]` | `None` | Button+modifier click bindings |
| `controls` | `dict` | `None` | Per-mouse-button camera actions |
| `cursor` | `str` | `None` | Initial CSS cursor over the canvas |

## `ImageData`

An image is a numpy pixel buffer or a URL:

```python
import numpy as np
from pytanga.viz import ImageData

data = np.zeros((200, 320, 3), dtype=np.uint8)   # H×W×3 RGB
image = ImageData("gradient", data=data)
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Image id |
| `data` | `np.ndarray \| None` | 2-D (H×W → 1 channel) or 3-D (H×W×C, C ∈ {1,3,4}) |
| `url` | `str \| None` | Alternative to `data`; then `width`/`height`/`channels`/`dtype` are required |
| `width` / `height` | `int` | Derived from `data`; required with `url` |
| `channels` | `int` | 1, 3, or 4 |
| `dtype` | `ImageDType` | `uint8`, `uint16`, or `float32` |

`data` and `url` are mutually exclusive.  A `pil_to_numpy` helper converts a PIL
image to the right numpy shape/dtype.

## Setting images

```python
canvas.set_image(image)    # replace layer 0, re-frame the camera
canvas.add_image(image2)   # append another layer (max 4)
```

`set_image` re-frames the 2D camera on the new image's pixel extent
(`fit_to_image`); `add_image` appends a layer without re-framing.  Up to four
layers are supported.

## The pixel frame and overlays

The canvas scene is a `space_dim=2` scene whose origin is the image's top-left
corner, with **x right** and **y down** — 1 unit = 1 pixel.  Draw overlays in
pixel coordinates with `add`:

```python
from pytanga.geometry import Point, Rectangle2D

ref = canvas.add(
    Rectangle2D.between(Point(40.0, 30.0, 0.0), Point(160.0, 120.0, 0.0)),
    color="#ff4444",
)
```

`add` returns a ref; remove it with `canvas.remove(ref)`, or `canvas.clear()`
every overlay.  You can also reach the scene handle directly via `canvas.handle`
(a `VizSceneHandle`) to use the full scene API, and the underlying `ImageView`
(via `canvas.image_view`) for its images/shader/uniform state.

## Showing the canvas

```python
viz.show(layout=canvas.scene_view())
viz.wait()
```

`scene_view()` returns a `SceneView` pane for the dedicated scene, so the canvas
can be shown alone or dropped into a `SplitView` next to other panes.  The scene
name is `canvas.scene_name` (auto-generated, e.g. `imgc0`).

## Complete example

`py/examples/viz/image/image_canvas.py` — a synthetic gradient with a pixel
rectangle overlay and a ctrl+drag brightness/contrast handler.
