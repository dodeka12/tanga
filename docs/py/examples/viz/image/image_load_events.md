# Banner notifications for image loading

**Keywords:** image · pyramid · tiles · loading · events · on_image_loaded · banner

Registers a large tiled image in an `~pytanga.viz.ImageCanvas` and wires
`~pytanga.viz.Visualizer.on_image_loaded`,
`~pytanga.viz.Visualizer.on_image_tile_load`, and
`~pytanga.viz.Visualizer.on_image_tile_loaded` to show a banner whenever
the browser starts or finishes loading a pyramid level — a "loading…" / "ready"
indicator driven entirely by frontend lifecycle events.

## Run

```bash
uv run python py/examples/viz/image/image_load_events.py
```

## Source

[`viz/image/image_load_events.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/image/image_load_events.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""image_load_events.py — Banner notifications for image loading.

Registers a large tiled image in an :class:`~pytanga.viz.ImageCanvas` and wires
:meth:`~pytanga.viz.Visualizer.on_image_loaded`,
:meth:`~pytanga.viz.Visualizer.on_image_tile_load`, and
:meth:`~pytanga.viz.Visualizer.on_image_tile_loaded` to show a banner whenever
the browser starts or finishes loading a pyramid level — a "loading…" / "ready"
indicator driven entirely by frontend lifecycle events.

Run with:  uv run python py/examples/viz/image/image_load_events.py

Keywords: image, pyramid, tiles, loading, events, on_image_loaded, banner
"""

from __future__ import annotations

import numpy as np

from pytanga.viz import (
    ControlEvent,
    ImageCanvas,
    ImageData,
    ImageStatusRecord,
    Visualizer,
)

WIDTH, HEIGHT = 4096, 2048


def _gradient(width: int, height: int) -> np.ndarray:
    """A 3-channel RGB gradient of shape (H, W, 3), dtype uint8."""
    xs = np.arange(width, dtype=np.float32)
    ys = np.arange(height, dtype=np.float32)
    t = (xs[None, :] + ys[:, None]) / max(width + height - 2, 1)
    out = np.zeros((height, width, 3), dtype=np.uint8)
    lo = t <= 0.5
    out[..., 0][lo] = ((1.0 - 2.0 * t[lo]) * 255).astype(np.uint8)
    out[..., 1][lo] = ((2.0 * t[lo]) * 255).astype(np.uint8)
    hi = ~lo
    out[..., 1][hi] = ((2.0 - 2.0 * t[hi]) * 255).astype(np.uint8)
    out[..., 2][hi] = ((2.0 * t[hi] - 1.0) * 255).astype(np.uint8)
    return out


def main() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)

    async def on_image_loaded(record: ImageStatusRecord, _event: ControlEvent) -> None:
        await viz.show_banner_async(
            f"Image ready — {record.source} {record.width}×{record.height}",
            title="Image loaded",
            auto_hide=False,
        )

    async def on_image_tile_load(
        record: ImageStatusRecord, _event: ControlEvent
    ) -> None:
        await viz.show_banner_async(
            f"Loading level {record.level}…", title="Image loading", auto_hide=False
        )

    async def on_image_tile_loaded(
        record: ImageStatusRecord, _event: ControlEvent
    ) -> None:
        await viz.show_banner_async(
            f"Level {record.level} loaded", title="Image loading", auto_hide=False
        )

    viz.on_image_loaded(on_image_loaded)
    viz.on_image_tile_load(on_image_tile_load)
    viz.on_image_tile_loaded(on_image_tile_loaded)

    pyramid = viz.register_image_pyramid(
        "gradient", _gradient(WIDTH, HEIGHT), tile_size=256
    )
    canvas = ImageCanvas(viz)
    canvas.set_image(ImageData("gradient", tiled=pyramid))
    viz.show(layout=canvas.scene_view())
    viz.wait()


if __name__ == "__main__":
    main()
````
