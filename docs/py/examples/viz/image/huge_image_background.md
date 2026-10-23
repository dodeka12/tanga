# zoom/pan a large tiled pane background

**Keywords:** image · background · pyramid · tiles · ImageView · CameraView · pinhole · navigation · zoom · pan · large image · split view · log view · events · on_image_loaded

Shows the same large, noisy gradient as `huge_image.py`, but as a calibrated
`~pytanga.viz.CameraView` `background_image` (`navigation="2d"`), so
the mouse wheel zooms into the image and dragging pans within it — the same
calibrated-pane interaction as `calibrated_labeling_app.py`.

A synthetic, distortion-free pinhole camera frames the image; a bound
`~pytanga.viz.ImageView` swaps in the full-resolution image via
`set_image`, which registers its on-demand tile pyramid with the
`~pytanga.viz.Visualizer` so the frontend fetches only the tiles it
needs from `/image/{id}/{level}/{x}/{y}`.  Per-pixel luminance noise makes the
pyramid resolution (and the on-demand loading of the higher-resolution tiles as
you zoom in) immediately visible.

The layout is a vertical `~pytanga.viz.SplitView`: the scene pane on top,
and a live `~pytanga.viz.LogView` at the bottom that logs the frontend
`image_loaded` / `image_tile_load` / `image_tile_loaded` lifecycle events
as you zoom in and out (via `Visualizer.on_image_*`).

## Run

```bash
uv run python py/examples/viz/image/huge_image_background.py
```

## Source

[`viz/image/huge_image_background.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/image/huge_image_background.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""huge_image_background.py — zoom/pan a large tiled pane background.

Shows the same large, noisy gradient as ``huge_image.py``, but as a calibrated
:class:`~pytanga.viz.CameraView` ``background_image`` (``navigation="2d"``), so
the mouse wheel zooms into the image and dragging pans within it — the same
calibrated-pane interaction as ``calibrated_labeling_app.py``.

A synthetic, distortion-free pinhole camera frames the image; a bound
:class:`~pytanga.viz.ImageView` swaps in the full-resolution image via
``set_image``, which registers its on-demand tile pyramid with the
:class:`~pytanga.viz.Visualizer` so the frontend fetches only the tiles it
needs from ``/image/{id}/{level}/{x}/{y}``.  Per-pixel luminance noise makes the
pyramid resolution (and the on-demand loading of the higher-resolution tiles as
you zoom in) immediately visible.

The layout is a vertical :class:`~pytanga.viz.SplitView`: the scene pane on top,
and a live :class:`~pytanga.viz.LogView` at the bottom that logs the frontend
``image_loaded`` / ``image_tile_load`` / ``image_tile_loaded`` lifecycle events
as you zoom in and out (via ``Visualizer.on_image_*``).

Run with:  uv run python py/examples/viz/image/huge_image_background.py

Keywords: image, background, pyramid, tiles, ImageView, CameraView, pinhole, navigation, zoom, pan, large image, split view, log view, events, on_image_loaded
"""

import numpy as np

from pytanga.geometry import Matrix, OpenCVFrame
from pytanga.viz import (
    CameraCalibration,
    CameraView,
    ControlEvent,
    ImageData,
    ImageStatusRecord,
    ImageView,
    LogView,
    SceneView,
    Size,
    SplitView,
    ViewportConfig,
    Visualizer,
)

WIDTH, HEIGHT = 8192, 4096
#: Focal length in pixels.  The background fit is driven by the image/pane
#: aspect, so this only needs to be a sensible positive value.
_FOCAL_PX = 4096.0


def _gradient(width: int, height: int, rng: np.random.Generator) -> np.ndarray:
    """A noisy 3-channel RGB gradient of shape (H, W, 3), dtype uint8.

    Red at top-left → green at the centre → blue at bottom-right, plus per-pixel
    luminance noise so zooming in reveals the full pyramid resolution and the
    on-demand loading of the higher-resolution tiles.
    """
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

    # Same luminance perturbation on R/G/B; apply in int16 so the clip never
    # wraps around.  A single-channel broadcast keeps the noise array small.
    noise = rng.integers(-24, 25, size=(height, width, 1), dtype=np.int16)
    acc = out.astype(np.int16)
    acc += noise
    np.clip(acc, 0, 255, out=acc)
    return acc.astype(np.uint8)


def _calibration(width: int, height: int) -> CameraCalibration:
    """A synthetic, distortion-free pinhole at the world origin looking along -z."""
    return CameraCalibration(
        K=Matrix(
            [
                [_FOCAL_PX, 0.0, width / 2.0],
                [0.0, _FOCAL_PX, height / 2.0],
                [0.0, 0.0, 1.0],
            ]
        ),
        R=Matrix(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ]
        ),
        t=[0.0, 0.0, 0.0],
        image_size=(width, height),
        frame=OpenCVFrame(),
        units=1.0,
    )


def main() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz.scene("world")

    cam = _calibration(WIDTH, HEIGHT).to_pinhole_camera()

    # Bind a small placeholder background first, so the pane exists and the
    # ImageView is attached to the layout before the large image is swapped in.
    bg = ImageView("gradient")
    bg.set_image(ImageData("gradient", data=np.zeros((64, 64, 3), np.uint8)))
    pane = SceneView(
        "world",
        camera_view=CameraView(
            cam,
            navigation="2d",
            viewport=ViewportConfig(zoom=1.0, pan=(0.0, 0.0)),
            background_image=bg,
        ),
    )

    # Bottom log pane: the frontend image lifecycle events are logged here as you
    # zoom in and out (image_loaded / image_tile_load / image_tile_loaded).
    log = LogView(id="log", max_history=200, show_date=True)
    log.log("Ready — zoom in to fetch higher-resolution tiles.")

    async def on_image_loaded(record: ImageStatusRecord, _event: ControlEvent) -> None:
        log.log(
            {
                "message": f"image_loaded  {record.source} {record.width}×{record.height}",
                "level": "info",
            }
        )

    async def on_image_tile_load(record: ImageStatusRecord, _event: ControlEvent) -> None:
        log.log(
            {"message": f"image_tile_load  level {record.level}", "level": "warn"}
        )

    async def on_image_tile_loaded(
        record: ImageStatusRecord, _event: ControlEvent
    ) -> None:
        log.log(
            {"message": f"image_tile_loaded  level {record.level}", "level": "info"}
        )

    viz.on_image_loaded(on_image_loaded)
    viz.on_image_tile_load(on_image_tile_load)
    viz.on_image_tile_loaded(on_image_tile_loaded)

    layout = SplitView(
        orientation="vertical",
        sizes=[Size.percent(70), Size.percent(30)],
        children=[pane, log],
    )
    viz.show(layout=layout)

    # Swap in the full-resolution noisy gradient after the viewer is up.  ImageData
    # auto-tiles it (a pyramid), and the bound view's self-push registers that
    # pyramid with the server so the frontend can fetch its tiles on demand.
    rng = np.random.default_rng(12345)
    bg.set_image(ImageData("gradient", data=_gradient(WIDTH, HEIGHT, rng)))

    viz.wait()


if __name__ == "__main__":
    main()
````
