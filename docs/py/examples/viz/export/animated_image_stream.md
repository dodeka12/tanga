# Export an animated noise image stream

**Keywords:** export · animated · image · noise · stream · jpeg · AnimationRecording

Records a stream of programmatic noise images (one new image per frame) and
exports it as an animated HTML with a play/pause/scrub playback engine.  Each
frame is captured with `capture_frame(include_images=True)` so the noise
image is re-embedded (JPEG) per frame.

## Run

```bash
uv run python py/examples/viz/export/animated_image_stream.py
```

## Source

[`viz/export/animated_image_stream.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/export/animated_image_stream.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""animated_image_stream.py — Export an animated noise image stream.

Records a stream of programmatic noise images (one new image per frame) and
exports it as an animated HTML with a play/pause/scrub playback engine.  Each
frame is captured with ``capture_frame(include_images=True)`` so the noise
image is re-embedded (JPEG) per frame.

Run with:  uv run python py/examples/viz/export/animated_image_stream.py

Keywords: export, animated, image, noise, stream, jpeg, AnimationRecording
"""

import numpy as np

from pytanga.viz import AnimStyle, ImageCanvas, ImageData, Visualizer

WIDTH, HEIGHT = 320, 240
FRAMES = 60


def _noise(rng: np.random.Generator) -> np.ndarray:
    """A programmatic RGB noise image of shape (H, W, 3), dtype uint8."""
    return rng.integers(0, 256, size=(HEIGHT, WIDTH, 3), dtype=np.uint8)


def main() -> None:
    rng = np.random.default_rng(0)
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
    canvas = ImageCanvas(viz)
    canvas.set_image(ImageData("noise", data=_noise(rng)))

    recording = canvas.handle.start_animation_recording()
    for _ in range(FRAMES):
        canvas.set_image(ImageData("noise", data=_noise(rng)))
        recording.capture_frame(include_images=True)

    canvas.handle.export_snapshot(
        "_output/animated_image_stream.html",
        overwrite=True,
        animation=recording,
        anim_style=AnimStyle(fps=15, loop=True, compress=True),
    )
    print("Exported _output/animated_image_stream.html — open it in any browser.")


if __name__ == "__main__":
    main()
````
