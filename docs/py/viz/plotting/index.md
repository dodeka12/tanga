# Plotting

The `CoordinateSystem` helper builds a complete plotting coordinate system —
grid, axes (with value labels), an optional background plane, and plotted
point paths — inside a single `VizGroup`. It is **not** a scene object itself;
it owns the group and the `VizObjectRef`s of the objects it creates, and
updates them in place when the axis ranges change.

| Guide | What you will learn |
|-------|---------------------|
| [Coordinate System](coordinate-system.md) | The `CoordinateSystem` helper: scales, `size`/`align`/`axis_origin`, live trails |
| [Coordinate System (examples)](coordinate-system.ipynb) | Runnable notebook showing the effect of several parameter combinations |
