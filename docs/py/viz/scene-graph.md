# Scene Graph & Transforms

The visualizer maintains an authoritative **scene graph** in Python. Every
drawable is a *node* that stores its own resolved style, geometry, and — for
scene-layer nodes — an explicit transform. The browser mirrors this hierarchy
in three.js and applies **partial, aspect-scoped updates** (`full` / `style` /
`transform`) in place, so moving or rotating a compound object never recomputes
or re-sends its geometry.

## Layers

Nodes live in one of two sub-graphs:

- **Scene layer** — geometric entities and operators. Scene nodes carry a
  canonical :class:`~pytanga.viz.Transform` (position + Euler ``"XYZ"`` rotation
  + scale) and participate in a parent/child tree. They render through a
  `THREE.Object3D` hierarchy.
- **Overlay layer** — labels, annotations, and titles. Overlay nodes carry a
  `position` anchor plus an optional `attach_to` scene-node reference and have
  **no** rotation or scale; they live in the screen/CSS plane and follow their
  target node.

The classes are :class:`~pytanga.viz.VizNode` (base),
:class:`~pytanga.viz.VizSceneObject`, :class:`~pytanga.viz.VizOverlayObject`,
and :class:`~pytanga.viz.VizGroup` (a container scene node with
`kind == "VizGroup"` and no entity/style).

## Creating groups and children

```python
from pytanga.geometry import Direction, Line, Point
from pytanga.viz import Visualizer

viz = Visualizer()
grp = viz.add_group("spinner")          # returns a VizObjectRef
grp.new(Point(0, 0, 0), color="#ff4444")
grp.new(Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)))
viz.run()
```

`viz.new(...)` is the same as `viz.add(...)` but returns a
:class:`~pytanga.viz.VizObjectRef` instead of a raw `str` id. The existing
`viz.add(...)` keeps its `str` return for backward compatibility.

## The `VizObjectRef` convenience wrapper

A :class:`~pytanga.viz.VizObjectRef` wraps a node and lets you mutate it without
tracking raw IDs. Property setters mark the correct dirty aspect automatically.

```python
ref = viz.new(Point(1, 2, 3))

ref.entity = Point(4, 5, 6)      # replaces geometry → "full" aspect
ref.style  = PointStyle(size=0.2)  # merges non-None style fields → "style"
ref.color  = "#00ff00"           # → "style"
ref.opacity = 0.5                # → "style"
```

### Transforms (scene nodes only)

```python
ref.translate(1, 0, 0)                       # or a Point / Direction / Translator
ref.rotate(angle=0.5, axis=(0, 0, 1))        # axis-angle, Euler "XYZ"
ref.scale_by(2.0)                            # uniform or component-wise
ref.set_transform(position=(1, 2, 3), rotation=(0, 0, 0), scale=(1, 1, 1))

# Operator-based transforms compose in local space:
from pytanga.geometry.operators import Motor, Rotor, Translator
ref.apply_transform(Rotor(angle=0.5, axis=Direction(0, 0, 1)))
ref.apply_transform(Motor(
    rotor=Rotor(angle=0.5, axis=Direction(0, 0, 1)),
    translator=Translator(vector=Direction(1, 0, 0)),
))
```

`ref.transform` exposes the node's underlying
:class:`~pytanga.viz.Transform` (with `.matrix()`, `.position`, `.rotation`,
`.scale`, `apply_matrix`, …), and `ref.world_matrix` returns the composed world
matrix through the parent chain.

### Labels & overlays

```python
point = viz.new(Point(0, 0, 0), label="origin")
point.label_ids            # IDs of labels attached to this node
point.labels               # list of VizObjectRef for those labels

label_ref = point.labels[0]
label_ref.text = "new text"
label_ref.position = (0.5, 0, 0)
label_ref.attach_to = other_node_id
label_ref.update_label(text="…", style=LabelStyle(...))
```

## Aspect-patch update model

Each node tracks which *aspects* changed and `flush()` emits an `object_update`
message with a list of patches:

| Aspect | Payload | Effect |
|--------|---------|--------|
| `full` | complete node dict (geometry + style + transform/parent) | create/replace |
| `style` | `{"style": {…}}` | merge the resolved style, re-apply materials |
| `transform` | `{"position", "rotation", "scale"}` | apply to the `Object3D` in place |

Rotating a :class:`~pytanga.viz.VizGroup` therefore emits a single `transform`
patch for the group — its children are **not** re-serialized and their vertices
are never recomputed.

```python
for angle in range(360):
    grp.set_transform(rotation=(0.0, 0.0, angle * 0.03))
    viz.flush()
    viz.sleep_ms(16)
```

## Run the example

```bash
uv run python py/examples/viz/demo_scene_graph.py
```
