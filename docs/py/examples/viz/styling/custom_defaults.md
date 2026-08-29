# Global default styles and per-call overrides

**Keywords:** styling · defaults · overrides · set_default_color

## Run

```bash
uv run python py/examples/viz/styling/custom_defaults.py
```

## Source

[`viz/styling/custom_defaults.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/styling/custom_defaults.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""custom_defaults.py — Global default styles and per-call overrides.

Run with:  uv run python py/examples/viz/styling/custom_defaults.py

Keywords: styling, defaults, overrides, set_default_color
"""

from pytanga.geometry import Direction, Line, Plane, Point, Sphere
from pytanga.viz import PointStyle, SphereStyle, Visualizer

viz = Visualizer(title="Tanga — Custom Defaults")

# Change default colors and extents
viz.set_default_color("point", (0.0, 1.0, 0.0))  # RGB tuple -> green
viz.set_default_color("line", (0.0, 1.0, 1.0))  # RGB tuple -> cyan
viz.set_default_color("plane", "#ff00ff")  # hex string -> magenta
viz.styles["Plane"].extent = 15.0

# These use the new defaults
viz.new(Point(2, 0, 0), style=PointStyle(size=0.15), label="green point (default)")
viz.new(
    Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)),
    label="cyan line (default)",
)
viz.new(
    Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)),
    opacity=0.25,
    label="magenta plane (default)",
)

# Per-entity override - red, ignores the global green default
viz.new(
    Point(0, 2, 0),
    color="#ff0000",
    style=PointStyle(size=0.15),
    label="red point (override)",
)

viz.new(
    Sphere(Point(0, 0, 0), radius=2.5),
    style=SphereStyle(wireframe=True),
    opacity=0.3,
    label="amber sphere (default)",
)

viz.show()
viz.wait()
````
