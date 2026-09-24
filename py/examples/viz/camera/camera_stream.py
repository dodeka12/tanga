# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""camera_stream.py — Stream a programmatic camera feed at 30 Hz over MJPEG.

Publishes random noise at 30 Hz through
:meth:`~pytanga.viz.Visualizer.register_camera_stream` and shows it in an
:class:`~pytanga.viz.ImageCanvas` backed by ``/stream/cam`` (MJPEG over HTTP,
decoupled from the WebSocket scene channel).

Run with:  uv run python py/examples/viz/camera/camera_stream.py

Keywords: camera, stream, mjpeg, noise, 30fps, register_camera_stream
"""

import numpy as np

from pytanga.viz import ImageCanvas, ImageData, ImageDType, Visualizer

WIDTH, HEIGHT = 640, 480


def main() -> None:
    rng = np.random.default_rng()
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
    print("Streaming noise at 30 fps (press q or Ctrl+C to stop).")
    for _ in viz.animate(fps=30):
        stream.publish(rng.integers(0, 256, size=(HEIGHT, WIDTH, 3), dtype=np.uint8))


if __name__ == "__main__":
    main()
