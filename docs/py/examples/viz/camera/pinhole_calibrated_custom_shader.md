# a custom GLSL shader on a calibrated image

**Keywords:** camera · pinhole · calibration · image background · custom shader · uniform · GLSL · RGB rotation · ctrl+drag

Loads one bundled BOP T-LESS training image plus its pinhole calibration and
shows it as a calibrated `CameraView.background_image` in a `2d`-navigation
pane, with a custom fragment shader that rotates each pixel's RGB vector around
the grayscale axis `(1,1,1)/√3`.  A custom `u_angle` uniform drives the
rotation; a ctrl+left-drag handler rotates the angle by the horizontal drag
distance (wrapping at 2π).  The shader is registered via
`~pytanga.viz.Visualizer.register_background_shader` and the uniform via
`~pytanga.viz.Visualizer.register_background_uniform` /
`~pytanga.viz.Visualizer.set_background_uniform`.

Unlike an `~pytanga.viz.ImageCanvas` shader (which receives a ready-made
`vUv`), a background fragment shader receives `vNdc` and must reproduce the
letterbox/crop UV mapping itself — see `docs/py/viz/image/background-shaders.md`.
Attribution: T-LESS, Hodan et al., WACV 2017, CC BY 4.0.

## Run

```bash
uv run python py/examples/viz/camera/pinhole_calibrated_custom_shader.py
```

## Source

[`viz/camera/pinhole_calibrated_custom_shader.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/camera/pinhole_calibrated_custom_shader.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pinhole_calibrated_custom_shader.py — a custom GLSL shader on a calibrated image.

Loads one bundled BOP T-LESS training image plus its pinhole calibration and
shows it as a calibrated ``CameraView.background_image`` in a ``2d``-navigation
pane, with a custom fragment shader that rotates each pixel's RGB vector around
the grayscale axis ``(1,1,1)/√3``.  A custom ``u_angle`` uniform drives the
rotation; a ctrl+left-drag handler rotates the angle by the horizontal drag
distance (wrapping at 2π).  The shader is registered via
:meth:`~pytanga.viz.Visualizer.register_background_shader` and the uniform via
:meth:`~pytanga.viz.Visualizer.register_background_uniform` /
:meth:`~pytanga.viz.Visualizer.set_background_uniform`.

Unlike an :class:`~pytanga.viz.ImageCanvas` shader (which receives a ready-made
``vUv``), a background fragment shader receives ``vNdc`` and must reproduce the
letterbox/crop UV mapping itself — see ``docs/py/viz/image/background-shaders.md``.
Attribution: T-LESS, Hodan et al., WACV 2017, CC BY 4.0.

Run with:  uv run python py/examples/viz/camera/pinhole_calibrated_custom_shader.py

Keywords: camera, pinhole, calibration, image background, custom shader, uniform, GLSL, RGB rotation, ctrl+drag
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from PIL import Image

from pytanga.geometry import Matrix, OpenCVFrame
from pytanga.viz import (
    CalibratedSurface,
    CameraCalibration,
    CameraView,
    DragBinding,
    DragEvent,
    ImageData,
    InteractionSurface,
    ModifierKey,
    MouseButton,
    SceneView,
    ViewportConfig,
    Visualizer,
)
from pytanga.viz.image import pil_to_numpy

_DATA_DIR = Path(__file__).resolve().parent / "data" / "tless"

#: Interaction-plane distance (metres) in front of the camera.
_DEPTH = 0.6

# Custom background fragment shader.  The standard vertex provides ``vNdc``, and
# the renderer always binds ``uImage`` plus the letterbox/crop uniforms; a custom
# uniform (``u_angle``) drives the RGB rotation.
_FRAGMENT = """
precision highp float;
varying vec2 vNdc;
uniform sampler2D uImage;
uniform float uImageAspect;   // image width / height
uniform float uPaneAspect;    // pane width / height
uniform float uFit;           // 0.0 = letterbox (fit), 1.0 = stretch (fill)
uniform vec4 uCrop;           // (u0, v0, u1, v1) normalized image coords
uniform float uHx;            // explicit zoom-scaled letterbox half-extent (NDC)
uniform float uHy;            // explicit zoom-scaled letterbox half-extent (NDC)
uniform float u_angle;

void main() {
    // Letterbox/crop UV mapping (mirrors the default background shader).
    float hx = uHx > 0.0 ? uHx : (uFit > 0.5 ? 1.0 : min(1.0, uImageAspect / uPaneAspect));
    float hy = uHy > 0.0 ? uHy : (uFit > 0.5 ? 1.0 : min(1.0, uPaneAspect / uImageAspect));
    vec2 q = vNdc / vec2(hx, hy);
    if (abs(q.x) > 1.0 || abs(q.y) > 1.0) {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    } else {
        vec2 p = q * 0.5 + 0.5;
        vec2 uv;
        uv.x = uCrop.x + p.x * (uCrop.z - uCrop.x);
        uv.y = 1.0 - uCrop.w + p.y * (uCrop.w - uCrop.y);
        vec3 rgb = texture2D(uImage, uv).rgb;

        // Rotate the RGB vector around the grayscale axis (1,1,1)/sqrt(3).
        vec3 axis = normalize(vec3(1.0));
        float c = cos(u_angle);
        float s = sin(u_angle);
        vec3 rotated = rgb * c
            + cross(axis, rgb) * s
            + axis * dot(axis, rgb) * (1.0 - c);

        gl_FragColor = vec4(clamp(rotated, 0.0, 1.0), 1.0);
    }
}
"""


def _load_calibration() -> tuple[dict[str, Any], ImageData]:
    """Load the bundled T-LESS image + calibration JSON."""
    data = json.loads((_DATA_DIR / "calibration.json").read_text(encoding="utf-8"))
    img = Image.open(_DATA_DIR / data["image"])
    img.load()
    return data, ImageData("camera", data=pil_to_numpy(img))


def main() -> None:
    data, background = _load_calibration()
    width, height = int(data["width"]), int(data["height"])

    # OpenCV-style calibration (K/R/t in millimetres) → a PinholeCamera in the
    # standard right-handed world (metres).
    calib = CameraCalibration(
        K=Matrix(data["K"]),
        R=Matrix(data["R_w2c"]),
        t=data["t_w2c"],
        image_size=(width, height),
        frame=OpenCVFrame(),
        units=0.001,  # T-LESS stores lengths in millimetres
    )
    cam = calib.to_pinhole_camera()

    viz = Visualizer(
        title="Tanga — Calibrated Background + Custom Shader (T-LESS)",
        add_default_axes=False,
        add_default_grid=False,
    )
    viz.scene("world")

    left = SceneView(
        "world",
        camera_view=CameraView(
            cam,
            navigation="2d",
            viewport=ViewportConfig(zoom=1.0, pan=(0.0, 0.0)),
            background_image=background,
        ),
    )

    # Swap in the custom RGB-rotation shader and seed its angle uniform.
    viz.register_background_shader(left, _FRAGMENT)
    viz.register_background_uniform(left, "u_angle", 0.0)

    # Ctrl+left-drag: horizontal movement → rotation angle (relative, wraps at 2π).
    angle = 0.0

    async def on_drag(event: DragEvent, _surface: InteractionSurface) -> bool:
        nonlocal angle
        dx = event.delta_pixels[0]
        angle = (angle + 0.02 * dx) % (2.0 * math.pi)
        viz.set_background_uniform(left, "u_angle", angle)
        return True

    left.surface = CalibratedSurface(
        calib,
        _DEPTH,
        drag_bindings=[DragBinding(MouseButton.LEFT, on_drag, ModifierKey.CTRL)],
    )

    viz.show(layout=left)
    viz.wait()


if __name__ == "__main__":
    main()
````
