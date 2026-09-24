# Image streams (camera feeds)

A 15–30 Hz camera feed is streamed over **MJPEG** (`multipart/x-mixed-replace`)
at `/stream/{id}`, decoupled from the WebSocket scene channel.  The server
encodes each frame as JPEG once and fans the latest frame out to subscribers.

## Register a stream

```python
import numpy as np
from pytanga.viz import ImageCanvas, ImageData, ImageDType, Visualizer

viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
stream = viz.register_camera_stream("cam", fps=30)

canvas = ImageCanvas(viz)
canvas.set_image(
    ImageData("cam", url="/stream/cam", width=640, height=480,
              channels=3, dtype=ImageDType.UINT8),
)
viz.show(layout=canvas.scene_view())

rng = np.random.default_rng()
for _ in viz.animate(fps=30):
    stream.publish(rng.integers(0, 256, size=(480, 640, 3), dtype=np.uint8))
```

- `stream.publish(image)` accepts a numpy array or an `ImageData` and encodes
  it as JPEG.
- Slow consumers simply receive the **newest** frame each tick — no backlog.
- Point any image layer / `CameraView.background_image` at a `/stream/…` URL to
  display the feed (the frontend uses a hidden `<img>` that browsers decode
  natively).
