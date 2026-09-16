# Composing Scene Subtrees

Sometimes you want to build a reusable **composed object** — a
:class:`~pytanga.viz.VizGroup` of :class:`~pytanga.viz.VizSceneObject` parts —
*before* you have a `Visualizer` (or a `Scene`) to put it in.  Typical cases:
a library of mechanical parts, a body assembled from base shapes
(cylinders, lines, …), or a scene graph built by another module and handed over
for display later.

You can build the whole subtree **detached** — with no scene or visualizer in
sight — and insert it in one step.  `viz.add(group)` / `viz.new(group)` then
registers the group **and every descendant**, so each part stays individually
addressable afterwards (`get_node`, `update`, `update_entity`, `remove`,
`set_interaction`).

## Building a detached subtree

`VizGroup` and `VizSceneObject` generate their own ids when you omit `id`, and a
child can carry a *partial* style — the missing fields are backfilled from the
scene's per-kind defaults at insert time:

```python
from pytanga.geometry import Cylinder, Direction, Line, Point
from pytanga.viz import (
    CylinderStyle,
    LineStyle,
    Visualizer,
    VizGroup,
    VizSceneObject,
)

group = VizGroup(name="flywheel")

# A cylinder hub — partial style, backfilled on insert.
group.add_child(
    VizSceneObject(
        None,  # auto-generated id
        Cylinder(origin=Point(0, 0, 0), axis=Direction(0, 0, 1),
                 length=1.2, radius=0.35, align_center=0.5),
        CylinderStyle(color="#88aaff"),
        kind="Cylinder",
    )
)

# A spoke line with a tip point.
group.add_child(
    VizSceneObject(
        None,
        Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0), length=1.5),
        LineStyle(color="#ff8855", thickness=3.0),
        kind="Line",
    )
)
group.add_child(
    VizSceneObject(
        None,
        Point(1.5, 0.0, 0.0),
        PointStyle(color="#44ff88", size=0.12),
        kind="Point",
    )
)
```

## Inserting the subtree

Only now does the visualizer need to exist:

```python
viz = Visualizer(title="Tanga — Composing a detached subtree")
viz.show()

ref = viz.new(group)      # registers the group and all descendants
ref.translate(0.0, 0.0, 0.5)

viz.flush()
```

After this, `group.id` is stable and every child is registered, so you can still
target a single part later:

```python
viz.update(child_id, opacity=0.5)
viz.update_entity(child_id, Point(9, 0, 0))
```

## Style contract

- Pass a style **instance** (e.g. `SphereStyle(color="#ffaa00")`) to get the
  remaining fields backfilled from the scene's per-kind defaults — identical to
  adding the part via `viz.add(...)`.
- A `style=None` child receives the full canonical defaults for its kind.
- Fully-resolved styles (including a `texture_label`) are preserved verbatim:

  ```python
  from pytanga.geometry import Point, Sphere
  from pytanga.viz import SphereStyle, TextureLabelStyle

  group.add_child(
      VizSceneObject(
          None,
          Sphere(center=Point(0, 0, 0), radius=1.0),
          SphereStyle(texture_label=TextureLabelStyle(text="S₁")),
          kind="Sphere",
      )
  )
  ```

## Limitations

- Detached subtrees carry **no labels**; attach labels after insertion (they
  reference the child ids that `add_subtree` assigns).
- A style passed as a plain `dict` is taken verbatim and is **not** merged with
  canonical defaults — pass a style instance for backfilling.

## See also

- [Scene Graph & Transforms](scene-graph.md) — the `VizGroup`/`VizObjectRef`
  model this builds on.
- Example: `py/examples/viz/scenes/compose_detached.py`.
