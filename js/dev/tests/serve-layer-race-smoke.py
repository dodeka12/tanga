# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""serve-layer-race-smoke.py — headless server for the background layer-texture
race Playwright smoke.

Reproduces the reported scenario: a bound :class:`~pytanga.viz.ImageView`
background with a black layer 0 and five 1×1 placeholder layers (indices 1..5).
A toolbar button, on each click, first resets layers 1..5 back to 1×1
placeholders and then replaces them in a row with full-size distinct opaque
colours (matching the reported ``set_layer`` loop), before enabling exactly one
layer (cycling 1→2→3→4→5).

Each replacement image is a uniform colour except its top-left pixel, which is
white.  A stale 1×1 decode (the bug) samples only that first pixel, so the whole
pane turns white where the uniform colour should be — the smoke asserts the pane
centre is the uniform colour.

Run with:  uv run python js/dev/tests/serve-layer-race-smoke.py
"""

from typing import Any

import numpy as np

from pytanga.geometry import Matrix, OpenCVFrame
from pytanga.viz import (
    ButtonView,
    CameraCalibration,
    CameraView,
    ControlEvent,
    ImageData,
    ImageLayerStyle,
    ImageView,
    SceneView,
    SplitView,
    ToolbarView,
    ViewportConfig,
    Visualizer,
)

WIDTH, HEIGHT = 512, 384
_FOCAL_PX = 512.0

#: Layer index → opaque RGB colour used to fill the replacement image.
_LAYER_COLORS: dict[int, tuple[int, int, int]] = {
    1: (255, 0, 0),
    2: (0, 255, 0),
    3: (0, 0, 255),
    4: (255, 255, 0),
    5: (255, 0, 255),
}


def _placeholder(index: int) -> ImageData:
    """The 1×1 RGBA placeholder layers 1..5 start as (disabled)."""
    return ImageData(f"layer{index}", data=np.zeros((1, 1, 4), dtype=np.uint8))


def _replacement(index: int) -> ImageData:
    """A full-size opaque RGBA colour with a white top-left marker pixel."""
    r, g, b = _LAYER_COLORS[index]
    data = np.full((HEIGHT, WIDTH, 4), (r, g, b, 255), dtype=np.uint8)
    data[0, 0] = (255, 255, 255, 255)
    return ImageData(f"layer{index}", data=data)


def _calibration() -> CameraCalibration:
    """A synthetic, distortion-free pinhole framing the image."""
    return CameraCalibration(
        K=Matrix(
            [
                [_FOCAL_PX, 0.0, WIDTH / 2.0],
                [0.0, _FOCAL_PX, HEIGHT / 2.0],
                [0.0, 0.0, 1.0],
            ]
        ),
        R=Matrix([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]),
        t=[0.0, 0.0, 0.0],
        image_size=(WIDTH, HEIGHT),
        frame=OpenCVFrame(),
        units=1.0,
    )


def main() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz.scene("world")

    bg = ImageView("bg")
    bg.set_image(ImageData("layer0", data=np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)))
    for i in range(1, 6):
        bg.add_layer(_placeholder(i), ImageLayerStyle(enabled=False))

    state: dict[str, int] = {"current": 0}

    async def _on_replace(_value: Any, _event: ControlEvent) -> None:
        # Reset to placeholders, then replace in a row — the sequence that races
        # the placeholder metadata against the full-size frames on the wire.
        for i in range(1, 6):
            bg.set_layer(i, _placeholder(i), ImageLayerStyle(enabled=False))
        for i in range(1, 6):
            bg.set_layer(i, _replacement(i), ImageLayerStyle(enabled=False))
        # Enable exactly one layer so the smoke can assert its colour.
        state["current"] = state["current"] % 5 + 1
        for i in range(1, 6):
            bg.set_layer_style(
                i, ImageLayerStyle(enabled=(i == state["current"]), opacity=1.0)
            )

    toolbar = ToolbarView(
        [ButtonView("btn_replace", label="Replace layers", on_click=_on_replace)]
    )
    pane = SceneView(
        "world",
        camera_view=CameraView(
            _calibration().to_pinhole_camera(),
            navigation="2d",
            viewport=ViewportConfig(zoom=1.0, pan=(0.0, 0.0)),
            background_image=bg,
        ),
    )
    layout = SplitView("vertical", [toolbar, pane])
    viz.set_layout(layout, name="demo")

    viz.start_server(host="localhost", port=0)
    print(f"SMOKE_URL={viz.url}", flush=True)
    viz.wait()


if __name__ == "__main__":
    main()
