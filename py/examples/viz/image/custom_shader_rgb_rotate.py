# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""custom_shader_rgb_rotate.py — Custom image shader that rotates RGB vectors.

Replaces the :class:`~pytanga.viz.ImageCanvas` standard shader with a custom
fragment shader that rotates each pixel's RGB vector in RGB space around the
grayscale axis ``(1,1,1)/√3``.  A custom ``u_angle`` uniform drives the
rotation; a left-drag handler rotates the angle by the horizontal drag
distance (wrapping at 2π).  The shader is registered via
:meth:`~pytanga.viz.ImageCanvas.register_shader` and the uniform via
:meth:`~pytanga.viz.ImageCanvas.register_uniform`.

Run with:  uv run python py/examples/viz/image/custom_shader_rgb_rotate.py

Keywords: image, ImageCanvas, custom shader, uniform, GLSL, RGB, rotation, drag
"""

import math

import numpy as np

from pytanga.viz import (
    DragBinding,
    DragEvent,
    ImageCanvas,
    ImageData,
    MouseButton,
    Visualizer,
)


# Custom fragment shader.  The standard vertex shader provides ``vUv``, and the
# renderer always binds ``uImage0`` (the image texture) and ``uImageSize``.
_FRAGMENT = """
precision highp float;
varying vec2 vUv;
uniform sampler2D uImage0;
uniform vec2 uImageSize;
uniform float u_angle;

void main() {
    // Nearest-neighbour sample in the pixel frame (no zoom interpolation).
    vec2 snap = (floor(vUv * uImageSize) + 0.5) / uImageSize;
    vec3 rgb = texture2D(uImage0, snap).rgb;

    // Rotate the RGB vector around the grayscale axis (1,1,1)/sqrt(3).
    vec3 axis = normalize(vec3(1.0));
    float c = cos(u_angle);
    float s = sin(u_angle);
    vec3 rotated = rgb * c
        + cross(axis, rgb) * s
        + axis * dot(axis, rgb) * (1.0 - c);

    gl_FragColor = vec4(clamp(rotated, 0.0, 1.0), 1.0);
}
"""


def _gradient(width: int, height: int) -> np.ndarray:
    """A 3-channel RGB gradient of shape (H, W, 3), dtype uint8."""
    ys, xs = np.mgrid[0:height, 0:width]
    r = (xs / max(width - 1, 1) * 255).astype(np.uint8)
    g = (ys / max(height - 1, 1) * 255).astype(np.uint8)
    b = np.full_like(r, 64)
    return np.stack([r, g, b], axis=-1)


def main() -> None:
    width, height = 320, 200
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)

    async def on_drag(event: DragEvent, canvas: ImageCanvas) -> bool:
        # Horizontal movement → rotation angle (relative, wraps at 2π).
        dx = event.delta_pixels[0]
        u = canvas.image_view.uniforms
        canvas.set_uniform("u_angle", (u["u_angle"] + 0.02 * dx) % (2.0 * math.pi))
        return True

    canvas = ImageCanvas(
        viz,
        drag_handlers=[DragBinding(MouseButton.LEFT, on_drag)],
    )
    canvas.register_shader(_FRAGMENT)
    canvas.register_uniform("u_angle", 0.0)
    canvas.set_image(ImageData("gradient", data=_gradient(width, height)))

    viz.show(layout=canvas.scene_view())
    viz.wait()


if __name__ == "__main__":
    main()
