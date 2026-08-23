# SDF Viewer

The `pytanga.viz.sdf` submodule provides a ray-marched, signed-distance-function
(SDF) viewer as an alternative to the mesh-based `pytanga.viz` viewer. Geometry
is rendered by ray-marching a fragment shader built for a three.js
`ShaderMaterial`, using the inigo-quilez SDF reference formulas.

It requires **WebGL2** — if unavailable, the viewer shows an in-page error
banner; there is no WebGL1 fallback. It is **3D only** (2D is deferred).

## Two rendering paths

1. **Analytic path** — geometry entities and operators are mapped to
   compositions of an SDF primitive library. Primitives are exposed directly as
   `SdfNode` objects (`sphere`, `box`, `cylinder`, `torus`, …) and grouped via
   `Composed`. `Point`→sphere, `Line`→segment, `Sphere`→sphere, `Rotor`→disc,
   `Translator`/`Direction`→arrow, `Dilator`→rings, `Motor`→disc+arrow, etc.
2. **Algebra path** — an MV is drawn by directly evaluating `ip(point, mv)` or
   `op(point, mv)` (chosen by the MV's algebra `opns` flag) and mapping the
   resulting multivector to a signed distance via a registered distance
   function. The MV is reduced to a partially-contracted product matrix `M` on
   the backend; the shader only embeds the ray point and does `M·a`, then
   applies a distance function and an opacity transfer.

## Quick start

```python
from pytanga.geometry import Point, Sphere
from pytanga.viz.sdf import SdfVisualizer

viz = SdfVisualizer()
viz.add(Sphere(Point(0, 0, 0), 1.0), color="#ffaa00")
viz.show()  # opens the SDF viewer in a browser
viz.wait()  # blocks until Ctrl+C
```

Raw MVs render through the same `add()` call (the algebra path):

```python
from pytanga.basis.pga3 import BasisPGA3
from pytanga.geometry import create_entity
from pytanga.geometry.entities import Direction, Plane, Point

pga3 = BasisPGA3(opns=True)
plane = create_entity(pga3, Plane(point=Point(0, 0, 0), normal=Direction(0, 0, 1)))
viz.add(plane, color="#44ff44", calibrate=True)  # calibrate → |∇d| ≈ 1
```

## Distance functions

The distance function is a **viewer-level** setting (one active at a time),
mapping the result coefficient vector `r[] = M·a` to a scalar:

| Name | Formula | Notes |
|------|---------|-------|
| `scalar_pseudo` | `r[0] + r[I] + ‖r_rest‖` | **default**; signed via scalar + pseudoscalar, plus the magnitude of every other grade |
| `magnitude` | `‖r‖` | unsigned; unsuited to boolean difference/intersection |
| `scalar` | `r[0]` | signed raw scalar |
| `grade` | `‖r restricted to grade k‖` | parametrized |
| `component` | `r[blade_id]` | a single result blade coefficient |

```python
viz.distance = "scalar_pseudo"  # default; try "magnitude" or "scalar"
```

`normalize` (default `True`) normalizes the MV before forming `M`.

### Rendering the algebra field

The algebra "distance" `distOf(M·a)` is the raw null-space measure — zero on the
entity, but *not* a signed distance function (its gradient `|∇d|` is not bounded
by 1 and can even grow, and closed entities have a stationary centre). The
viewer therefore uses a **local-gradient step rule for algebraic objects only**:

```glsl
t += d / max(|∇d|, 1.0)     // mv_sdf objects
t += d                      // analytic objects (proper SDFs, unchanged)
```

This is the per-point first-order distance to the surface, so it never overshoots
while preserving the exact null-space zero-set. `calibrate=True` (a single global
scale) is still available to re-scale the field, but it is no longer required for
correct rendering.

Zero-thickness MVs (a line, a point) have a 1D/0D zero-set that the raymarcher
cannot hit; pass `thickness=` (a distance cutoff) to render them as a tube/ball:

```python
viz.add(line_mv, color="#ffaa00", calibrate=True, thickness=0.1)
```

The shader evaluates `d = distOf(M·a)·scale − thickness`.

### Soft opacity (distance-dependent, per object)

Each algebraic object can get a soft, distance-dependent opacity edge, independent
of the viewer-level opacity transfer:

```python
viz.add(
    line_mv,
    color="#ffaa00",
    calibrate=True,
    thickness=0.1,      # solid core radius
    falloff=0.15,       # exponential density falloff scale (Beer–Lambert)
    max_distance=0.5,   # hard cutoff: density is zero beyond this distance
)
```

The density outside the core is `σ(d) = exp(−d/falloff)/falloff`, hard-clipped to
zero at `max_distance` (default `5·falloff` when unset). The raymarcher integrates
this along the ray (`transmittance = exp(−∫σ dt)`), so a grazing ray renders a
soft translucent edge that fades to transparent — `falloff` sets how quickly it
fades (exponential), `max_distance` sets where it is hard-cut off. `falloff=0`
(default) keeps a hard surface.

## Opacity transfers

The distance is mapped to opacity through a selectable transfer function:

| Name | Formula | Effect |
|------|---------|--------|
| `step` | `d < ε ? 1 : 0` | crisp solid (default) |
| `linear` | `clamp(1 − d/ε, 0, 1)` | soft band |
| `sigmoid` | `1 − 1/(1 + exp(−d/ε))` | smooth soft edge |

The per-object `opacity` doubles as the falloff breadth `ε` (and the surface
alpha for `step`):

```python
viz.opacity = "sigmoid"
viz.add(Sphere(Point(0, 0, 0), 1.0), color="#ffaa00", opacity=0.6)
```

## Boolean combine modes

A signed distance is negative inside; per-object `combine` (or the `polarity`
shorthand) folds an object into the composed SDF:

- **union** `min(dA, dB)` — inside either (default).
- **intersection** `max(dA, dB)` — inside both.
- **difference** `max(dA, −dB)` — inside A, not inside B (`combine="subtract"`).

```python
viz.add(Sphere(Point(0, 0, 0), 1.5), color="#ffaa00")
viz.add(Sphere(Point(0.9, 0.5, 0), 0.8), combine="subtract")   # carve a cavity
viz.add(Sphere(Point(-1.1, 0, 0), 1.2), color="#44aaff", combine="intersection")
```

Smooth variants (`smooth_union` / `smooth_intersection` / `smooth_subtract`)
use the `vec2` smooth combinators for the distance, with a per-object
`smoothness` knob. `subtract`/`intersection` require a signed distance function
(`scalar_pseudo` or `scalar`); the unsigned `magnitude` mode is unsuited to
them and triggers a warning.

## Examples

| Script | Topic |
|--------|-------|
| [`demo_sdf_entities.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_sdf_entities.py) | Analytic entities (line + sphere − sphere) |
| [`demo_sdf_composed.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_sdf_composed.py) | `Composed` objects + the primitive library |
| [`demo_sdf_algebra.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_sdf_algebra.py) | Algebra (MV) path with mixed algebras |
| [`demo_sdf_booleans.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_sdf_booleans.py) | Per-object `combine=` / `polarity=` |
| [`demo_sdf_opacity.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_sdf_opacity.py) | Distance → opacity transfers |

Run with `uv run python py/examples/viz/<script>.py`.
