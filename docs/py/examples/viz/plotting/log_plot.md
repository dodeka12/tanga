# logarithmic plotting with CoordinateSystem

**Keywords:** plotting · CoordinateSystem · log plot

Builds a log-log coordinate system with `~pytanga.viz.CoordinateSystem`.
The world stays linear, but the axis value labels and grid spacing are
logarithmic.  `plot()` maps data through the scales automatically, and
`vline`/`hline` draw annotation lines at fixed data values.

## Run

```bash
uv run python py/examples/viz/plotting/log_plot.py
```

## Source

[`viz/plotting/log_plot.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/plotting/log_plot.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""log_plot.py — logarithmic plotting with CoordinateSystem.

Builds a log-log coordinate system with :class:`~pytanga.viz.CoordinateSystem`.
The world stays linear, but the axis value labels and grid spacing are
logarithmic.  ``plot()`` maps data through the scales automatically, and
``vline``/``hline`` draw annotation lines at fixed data values.

Run with:  uv run python py/examples/viz/plotting/log_plot.py

Keywords: plotting, CoordinateSystem, log plot
"""

from pytanga.viz import CoordinateSystem, PointPathStyle, Visualizer

viz = Visualizer(
    title="Tanga — Log-Log Plot",
    space_dim=2,
    add_default_axes=False,
    add_default_grid=False,
)

cs = CoordinateSystem(
    viz,
    xlim=(0.1, 1000.0),
    ylim=(1.0, 1_000_000.0),
    xscale="log",
    yscale="log",
    labels=("frequency", "power"),
)

# A power law y = x^2, sampled log-spaced on x.
xs = [0.1 * (10 ** (0.1 * i)) for i in range(40)]
ys = [x * x for x in xs]
cs.plot(xs, ys, color="#ffcc00", style=PointPathStyle(line_thickness=3))

# Annotation lines at fixed data values (log axes map the endpoints).
cs.vline(x=100.0, name="freq", color="#44aaff")
cs.hline(y=1000.0, name="power", color="#ff44ff")

viz.show()
viz.wait()
````
