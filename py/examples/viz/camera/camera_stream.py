# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""camera_stream.py — Stream a programmatic camera feed at 30 Hz over MJPEG.

Publishes frames at 30 Hz through
:meth:`~pytanga.viz.Visualizer.register_camera_stream` and shows it in an
:class:`~pytanga.viz.ImageCanvas` backed by ``/stream/cam`` (MJPEG over HTTP,
decoupled from the WebSocket scene channel).

Each frame is a red→green→blue ramp along the diagonal from top-left to
bottom-right (with a slowly moving highlight so the live feed is visible), so
any vertical flip is immediately visible.

Run with:  uv run python py/examples/viz/camera/camera_stream.py

Keywords: camera, stream, mjpeg, 30fps, register_camera_stream
"""

import numpy as np

from pytanga.viz import ImageCanvas, ImageData, ImageDType, Visualizer

WIDTH, HEIGHT = 640, 480


def _gradient_frame(phase: float) -> np.ndarray:
    """A diagonal red→green→blue ramp (uint8, H×W×3) with a moving highlight."""
    xs = np.arange(WIDTH, dtype=np.float32)
    ys = np.arange(HEIGHT, dtype=np.float32)
    t = (xs[None, :] + ys[:, None]) / max(WIDTH + HEIGHT - 2, 1)
    out = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    lo = t <= 0.5
    out[..., 0][lo] = ((1.0 - 2.0 * t[lo]) * 255).astype(np.uint8)
    out[..., 1][lo] = ((2.0 * t[lo]) * 255).astype(np.uint8)
    hi = ~lo
    out[..., 1][hi] = ((2.0 - 2.0 * t[hi]) * 255).astype(np.uint8)
    out[..., 2][hi] = ((2.0 * t[hi] - 1.0) * 255).astype(np.uint8)

    # A bright band that sweeps the diagonal so the stream is visibly live.
    band = np.abs(t - ((phase % 1.0) * 1.4 - 0.2)) < 0.02
    out[band] = np.clip(out[band].astype(np.int16) + 90, 0, 255)
    return out


def main() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
    stream = viz.register_camera_stream("cam", fps=30)
    canvas = ImageCanvas(viz)
    canvas.set_image(
        ImageData(
            "cam",
            url="/stream/cam",
            width=WIDTH,
            height=HEIGHT,
            channels=3,
            dtype=ImageDType.UINT8,
        )
    )
    viz.show(layout=canvas.scene_view())
    print("Streaming at 30 fps (press q or Ctrl+C to stop).")
    for i, _ in enumerate(viz.animate(fps=30)):
        stream.publish(_gradient_frame(i / 30))


if __name__ == "__main__":
    main()
