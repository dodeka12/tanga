# Export a programmatic image as HTML with JPEG compression

**Keywords:** export · image · jpeg · ImageCanvas · ImageData · html

Builds an RGB noise image, shows it in an `~pytanga.viz.ImageCanvas`,
and exports it as a self-contained HTML snapshot.  8-bit images are embedded as
JPEG data URLs by default, so the exported file stays small.

## Run

```bash
uv run python py/examples/viz/export/image_export.py
```

## Source

[`viz/export/image_export.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/export/image_export.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""image_export.py — Export a programmatic image as HTML with JPEG compression.

Builds an RGB noise image, shows it in an :class:`~pytanga.viz.ImageCanvas`,
and exports it as a self-contained HTML snapshot.  8-bit images are embedded as
JPEG data URLs by default, so the exported file stays small.

Run with:  uv run python py/examples/viz/export/image_export.py

Keywords: export, image, jpeg, ImageCanvas, ImageData, html
"""

import numpy as np

from pytanga.viz import ImageCanvas, ImageData, Visualizer

WIDTH, HEIGHT = 640, 480


def _noise(rng: np.random.Generator) -> np.ndarray:
    """A programmatic RGB noise image of shape (H, W, 3), dtype uint8."""
    return rng.integers(0, 256, size=(HEIGHT, WIDTH, 3), dtype=np.uint8)


def main() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
    canvas = ImageCanvas(viz)
    canvas.set_image(ImageData("noise", data=_noise(np.random.default_rng(0))))

    canvas.handle.export_snapshot("_output/image_export.html", overwrite=True)
    print("Exported _output/image_export.html — 8-bit image embedded as JPEG.")


if __name__ == "__main__":
    main()
````
