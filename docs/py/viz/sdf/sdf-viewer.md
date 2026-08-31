# SDF Viewer

The `pytanga.viz.sdf` submodule provides a ray-marched, signed-distance-function
(SDF) viewer as an alternative to the mesh-based `pytanga.viz` viewer. Geometry
is rendered by ray-marching a fragment shader built for a three.js
`ShaderMaterial`, using the inigo-quilez SDF reference formulas.

It requires **WebGL2** — if unavailable, the viewer shows an in-page error
banner; there is no WebGL1 fallback. It is **3D only** (2D is deferred).

> **Note:** this fullscreen SDF viewer is unchanged. The *standard* viewer's
> per-object SDF path gained per-entity styles, `SdfObject`/operators, and
> per-object materials — see
> [SDF Objects in the Standard Viewer](sdf-objects.md).


## Rendering path

Geometry entities and operators are mapped to compositions of an SDF primitive
library. Primitives are exposed directly as `SdfNode` objects (`sphere`, `box`,
`cylinder`, `torus`, …) and grouped via `Composed`. `Point`→sphere,
`Line`→segment, `Sphere`→sphere, `Rotor`→disc, `Translator`/`Direction`→arrow,
`Dilator`→rings, `Motor`→disc+arrow, etc. Raw multivectors passed to `add()` are
resolved through `geometry.analyze()` and rendered as their recognized geometric
entity.

## Quick start

```python
from pytanga.geometry import Point, Sphere
from pytanga.viz.sdf import SdfVisualizer

viz = SdfVisualizer()
viz.add(Sphere(Point(0, 0, 0), 1.0), color="#ffaa00")
viz.show()  # opens the SDF viewer in a browser
viz.wait()  # blocks until Ctrl+C
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
`smoothness` knob.

## Examples

| Script | Topic |
|--------|-------|
| [`entities.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/sdf/entities.py) | Analytic entities (line + sphere − sphere) |
| [`composed.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/sdf/composed.py) | `Composed` objects + the primitive library |
| [`booleans.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/sdf/booleans.py) | Per-object `combine=` / `polarity=` |

Run with `uv run python py/examples/viz/sdf/<script>.py`.
