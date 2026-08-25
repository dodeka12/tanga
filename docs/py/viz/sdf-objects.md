# SDF Objects in the Standard Viewer

The standard `pytanga.viz` viewer (the mesh-based Three.js viewer) can render
*some* scene objects as smooth, ray-marched signed-distance-field (SDF) solids,
mixed with the normal vertex/mesh pipeline in the same scene. The opt-in is a
marker style class, `SdfStyle`, passed to `Visualizer.add(...)`:

```python
from pytanga.geometry import Point, Sphere
from pytanga.viz import SdfStyle, Visualizer

viz = Visualizer()
viz.add(Sphere(Point(0, 0, 0), 1.0), color="#4477cc")                 # normal mesh
viz.add(Sphere(Point(2.5, 0, 0), 1.1), style=SdfStyle(color="#ffaa00"))  # ray-marched
viz.show()
viz.wait()
```

## `SdfStyle`

`SdfStyle` is a *marker* style: applying it opts that one entity into
ray-marched SDF rendering (`kind:"sdf"` on the wire) instead of the normal mesh
renderer. `color`/`opacity` still resolve through the normal priority chain
(per-entity props > style > canonical > builtin); the remaining fields are
SDF-specific knobs:

| Field          | Type   | Default | Meaning                                        |
|----------------|--------|---------|------------------------------------------------|
| `color`        | `str`  | `None`  | Optional override color (CSS hex).             |
| `opacity`      | `float`| `None`  | Optional override opacity (0..1).              |
| `soft_shadows` | `bool` | `True`  | Enable soft self-shadowing in the ray-marcher. |
| `max_steps`    | `int`  | `256`   | Ray-march step budget.                         |
| `bound_padding`| `float`| `0.05`  | Inflate the proxy AABB (any over-estimate is safe). |

## Per-object CSG with `Composed`

A single SDF object can be internally `Composed` — its own combinator tree
(e.g. a bead with a drilled hole).

```python
from pytanga.viz import SdfStyle, Visualizer
from pytanga.viz.sdf import Composed, capped_cylinder, sphere

bead = Composed(
    sphere(0.7),
    (capped_cylinder(1.0, 0.45), "subtract"),
)
viz.add(bead, style=SdfStyle(color="#44ff44"))
```

## Groups with `SdfGroup`

`SdfGroup` bundles several members into **one** ray-marched solid, so
cross-object CSG (`union`/`intersection`/`subtract`), smooth shading, and
self-shadowing all work *across* the members — while each member keeps an
independent runtime transform that can be animated separately (no shader
recompile). The proxy bounding box is the union of the members' AABBs and
resizes dynamically as they move.

Members may carry an optional `id` (every SDF constructor accepts an `id=…`
keyword), so a member can be addressed by name or by 0-based index:

```python
from pytanga.viz import SdfStyle, Visualizer
from pytanga.viz.sdf import SdfGroup, capped_cylinder, sphere

group = SdfGroup(
    sphere(1.0, position=(-1.0, 0.0, 0.0), id="left"),
    sphere(1.0, position=(1.0, 0.0, 0.0), id="orbit"),
    (capped_cylinder(1.5, 0.35), "subtract"),   # cut through both spheres
)
sdf_grp = viz.new(group, style=SdfStyle(color="#ffaa00"))

# Animate a member independently — by id or by index, frame-by-frame.
sdf_grp.set_member_transform("orbit", position=(1.5, 0.4, 0.0))
viz.flush()
```

`viz.new(…)` returns a `VizObjectRef`; `sdf_grp.entity` is the `SdfGroup`
itself, and `sdf_grp.set_member_transform(…)` is equivalent to
`viz.update_sdf_group_member(sdf_grp.id, …)`. Mutating directly through
`sdf_grp.entity.set_member_transform(…)` also marks the node dirty, so either
style works with a following `flush()`.

## Limitations

- **Member cap** — an `SdfGroup` supports up to 16 members (a compile-time
  uniform-array bound).
- **Mutual shadows deferred** — SDF objects get soft *self*-shadowing within an
  object/group, but do not cast or receive shadows onto *other* scene objects.
- **WebGL2 required** — SDF objects need GLSL3 + `gl_FragDepth`. On WebGL1 they
  are skipped (hidden) and a single yellow warning banner is shown; the standard
  mesh pipeline keeps working.

## Example

| Script | Topic |
|--------|-------|
| [`objects.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/sdf/objects.py) | Mix standard meshes with SDF-styled objects (sphere + `Composed` bead + tween + interaction) |
| [`group.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/sdf/group.py) | `SdfGroup` with per-member CSG + independent member animation |

Run with `uv run python py/examples/viz/sdf/<script>.py`.
