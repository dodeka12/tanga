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

## Automatic tiling

For most cases you don't need to register the pyramid yourself — `ImageData`
converts any array whose longest side exceeds 4096 px (or whose byte size
exceeds 32 MB) into an on-demand pyramid automatically:

```python
canvas.set_image(ImageData("noise", data=noise))
```

The thresholds are configurable (`tile_max_dim` / `tile_max_bytes`, defaults
`4096` / `32 * 1024 * 1024`) and the tile edge via `tile_size` (default `256`).
Pass `tile_max_dim=None, tile_max_bytes=None` to opt out.  The explicit
`register_image_pyramid` call above remains useful when you want a specific
`image_id` or to pre-register the route yourself.

## Display formats

Tiles are served as `jpeg` (8-bit display), `png` (lossless 16-bit), `raw`
(raw bytes), or `zlib` (lossless compressed raw) depending on the image dtype
and the requested `?format=`.  The frontend composes the best-fitting level
(long side ≤ 2048 px) into a single texture for pan/zoom: `uint8` images draw
JPEG/PNG tiles into an 8-bit canvas, while `float32`/`uint16` images fetch
`zlib` tiles and assemble them into a **float** texture — so the value range
(`u_value_min`/`u_value_max`) and brightness/contrast use the full dynamic range
instead of clipping to 8 bits.
