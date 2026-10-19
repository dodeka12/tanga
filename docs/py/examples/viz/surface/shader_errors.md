# Capture a shader compile error and show it in a banner

**Keywords:** shader error · compile error · banner · scrollable banner · client log · surface · debug

Adds a sphere with a deliberately broken custom surface shader, registers a
`viz.on_shader_error` handler, and shows the driver's compile error (with
source context) in a scrollable banner — the full frontend → backend → frontend
round-trip over the `client_log` channel.

## Run

```bash
uv run python py/examples/viz/surface/shader_errors.py
```

## Source

[`viz/surface/shader_errors.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/surface/shader_errors.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""shader_errors.py — Capture a shader compile error and show it in a banner.

Adds a sphere with a deliberately broken custom surface shader, registers a
``viz.on_shader_error`` handler, and shows the driver's compile error (with
source context) in a scrollable banner — the full frontend → backend → frontend
round-trip over the ``client_log`` channel.

Run with:  uv run python py/examples/viz/surface/shader_errors.py

Keywords: shader error, compile error, banner, scrollable banner, client log, surface, debug
"""

from __future__ import annotations

from typing import Any

from pytanga.geometry import Point, Sphere
from pytanga.viz import SurfaceMaterial, SurfaceShader, Visualizer

# `baseColor + ;` is a GLSL syntax error — the shader compiles lazily on the
# first render, which triggers `renderer.debug.onShaderError` → `sendLog`.
_BROKEN_FRAGMENT = """
vec3 surfaceColor(vec3 baseColor, vec3 n, vec3 p) {
    return baseColor + ;
}
"""


def main() -> None:
    viz = Visualizer(title="Tanga — Shader error reporting")

    async def _on_shader_error(record: Any, _event: Any) -> None:
        error = record.data.get("error", record.message) if record.data else record.message
        viz.show_banner(
            f"**Shader compile failed**\n\n```\n{error}\n```",
            title="Shader error",
            align_x=0.5,
            align_y=0.1,
            scrollable=True,
        )

    viz.on_shader_error(_on_shader_error)

    viz.add(
        Sphere(Point(0.0, 0.0, 0.0), 1.0),
        surface=SurfaceMaterial(shader=SurfaceShader("broken", _BROKEN_FRAGMENT)),
        label="broken shader",
    )

    viz.show()
    viz.wait()


if __name__ == "__main__":
    main()
````
