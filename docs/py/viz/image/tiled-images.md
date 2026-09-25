# Tiled images (very large images)

A very large image (a 360° panorama, whole-slide scan, or big programmatic
array) is too big to send in one frame.  Instead register it as an
**on-demand tile pyramid**, and the frontend fetches only the tiles it needs
from `/image/{id}/{level}/{x}/{y}`.

## Register a pyramid

```python
import numpy as np
from pytanga.viz import ImageCanvas, ImageData, Visualizer

viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
noise = np.random.default_rng().integers(0, 256, size=(4096, 8192, 3), dtype=np.uint8)
pyramid = viz.register_image_pyramid("noise", noise, tile_size=256)

canvas = ImageCanvas(viz)
canvas.set_image(ImageData("noise", tiled=pyramid))
viz.show(layout=canvas.scene_view())
```

- `tile_size` (default `256`) is the square tile edge; level 0 is the full
  resolution, and each level halves the dimensions.
- The image stays in memory once; tiles are encoded on demand and cached in a
  bounded LRU, so **multiple connected browsers** requesting the same viewport
  share the work (a pull model — each client fetches its own tiles, and
  identical tiles cache-hit).

## Display formats

Tiles are served as `jpeg` (8-bit display), `png` (lossless 16-bit), or `raw`
(raw bytes) depending on the image dtype and the requested `?format=`.  The
frontend composes the best-fitting level (long side ≤ 2048 px) into a single
texture for pan/zoom.
