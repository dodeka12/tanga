# Nested animation loops honoring Ctrl+C

**Keywords:** animation · nested loops · Ctrl+C · sweep

Drives an animation with two nested loop variables (a parameter sweep) instead
of the single flat loop that `animate()` provides.  Uses `sleep_ms()` to
pace each frame and `interrupted()` to break out cleanly on Ctrl+C.

## Run

```bash
uv run python py/examples/viz/animation/nested_sweep.py
```

## Source

[`viz/animation/nested_sweep.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/animation/nested_sweep.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""nested_sweep.py — Nested animation loops honoring Ctrl+C.

Drives an animation with two nested loop variables (a parameter sweep) instead
of the single flat loop that ``animate()`` provides.  Uses ``sleep_ms()`` to
pace each frame and ``interrupted()`` to break out cleanly on Ctrl+C.

Run with:  uv run python py/examples/viz/animation/nested_sweep.py

Keywords: animation, nested loops, Ctrl+C, sweep
"""

import math

from pytanga.geometry import Point
from pytanga.viz import Visualizer

viz = Visualizer(title="Tanga — Nested Sweep")
viz.show()

point = viz.new(Point(0, 0, 0), color="#ff4444", label="sweep")
viz.flush()

print("Sweeping two variables until Ctrl+C...")
try:
    for a in range(64):
        for b in range(64):
            u = a * 0.1
            v = b * 0.1
            point.entity = Point(
                3 * math.cos(u) * math.cos(v),
                3 * math.sin(u) * math.cos(v),
                2 * math.sin(v),
            )
            viz.flush()
            if not viz.sleep_ms(16):  # False == interrupted
                break
        if viz.interrupted():  # True == interrupted
            break
finally:
    viz.stop_server()

print("Animation stopped.")
````
