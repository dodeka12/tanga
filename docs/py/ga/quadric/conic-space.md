# Conic space — usage & visualization

A conic (2D) or quadric (3D) is the zero set of a symmetric quadratic form

```text
xᵀ A x = 0,    A = [[Q, b], [bᵀ, c]]
```

Perwass's *conic space* linearises this: the symmetric matrix becomes a vector,
so conics/quadrics live in a linear space that a geometric algebra can act on.
`pytanga.quadric` uses `BasisQ2` / `BasisQ3` (see [Bases](bases.md)).

## Point embedding

A point embeds as the rank-1 matrix `x xᵀ`, rescaled so the Euclidean inner
product with a coefficient vector is `½ xᵀ A x`:

- 2D: `x b1 + y b2 + (√2/2) b3 + (√2/2)x² b4 + (√2/2)y² b5 + xy b6`
- 3D: `x b1 + y b2 + z b3 + (√2/2) b4 + (√2/2)x² b5 + (√2/2)y² b6 + (√2/2)z² b7 + xy b8 + xz b9 + yz b10`

```python
from pytanga.quadric import embed_point

mv = embed_point(Q3, x, y, z)          # grade-1 OPNS blade
```

The key identity is `<coeff(A), embed(x)> = ½ xᵀ A x`, so the point lies on the
conic/quadric exactly when this inner product is zero.

## Coefficients ↔ matrix

`to_coeffs` / `from_coeffs` are exact inverses with a fixed ordering:

- conic (3×3): `(a13, a23, (√2/2)a33, (√2/2)a11, (√2/2)a22, a12)`
- quadric (4×4): `(q14, q24, q34, (√2/2)q44, (√2/2)q11, (√2/2)q22, (√2/2)q33, q12, q13, q23)`

`Conic` / `Quadric3D` are thin dataclasses over that vector; `.matrix` rebuilds
the symmetric matrix and classification properties (`kind`, `rank`,
`signature`, `center`, `eigenvalues`, `principal_directions`, `rho`) read the
affine block form.

## Reconstructing from points

A conic through 5 points (or a quadric through 9) is the **join** of the point
embeddings — the smallest OPNS blade containing them all:

```python
Q3 = BasisQ3(opns=True)
geo = Geometry(Q3)

p1 = geo(Point(2.0, 0.0, 0.0))
p2 = geo(Point(-1.0, 1.2, 0.0))
# … seven more …
quadric = p1 ^ p2 ^ p3 ^ p4 ^ p5 ^ p6 ^ p7 ^ p8 ^ p9   # grade-9 OPNS blade

viz.new(quadric)   # the visualizer analyzes the MV and draws the quadric
```

There are also direct helpers that return the symmetric matrix:

```python
from pytanga.quadric import conic_from_points, quadric_from_points

matrix = quadric_from_points(Q3, points)          # 4×4 symmetric matrix
```

The `*_from_points_svd` variants take the null space of the stacked embeddings
instead (more robust to noise).  A matrix becomes a drawable entity via
`Quadric3D(to_coeffs(matrix))`.

## Analysis and refinement

`analyze_entity` (or `Geometry.analyze`) normalises IPNS input to OPNS and
dispatches on the blade grade:

| space | OPNS grade | entity |
|---|---|---|
| Q2 | 1 | `Point` |
| Q2 | 2–4 | `PointSet` |
| Q2 | 5 | `Conic` |
| Q3 | 1 | `Point` |
| Q3 | 2–7 | `PointSet` |
| Q3 | 8 | degenerate intersection (`PlaneConicPair` / `Curve`) |
| Q3 | 9 | `Quadric3D` |

`Conic.refine()` / `Quadric3D.refine()` (and `Geometry.refine`) classify the
matrix and build the concrete entity — `Ellipse`, `Hyperbola`, `Parabola`,
`Cone`, `Ellipsoid`, `PlanePair`, … — via eigen-decomposition.

## The rotation rotor

Rotations act as versors `A ↦ R A R̃`.  `create_rotor` builds `R` from an angle
and axis; `analyze_rotor` inverts it back to `Rotor(angle, axis)`.  With
`Geometry`, a `Rotor` entity materialises the versor:

```python
rotor = geo(Rotor(angle, Direction(0, 0, 1)))   # an MV (even versor)
rotated = rotor.vp(conic)                        # R · conic · R̃
```

- Q2: `R = R2 R1` (grades {0,2,4}).
- Q3: three commuting factors `R_lin · R_mixed · R_quad` acting on the linear,
  mixed-quadratic and traceless-quadratic monomials at rates θ, θ, 2θ (grades
  {0,2,4,6}).

The full derivation is in `dev/theory/quadric-rotor-derivation.md`.

## Visualization

Conics and quadrics reach the viewer as concrete entities:

- A **`Quadric3D`** renders through the analytic **ray** path (`RayStyle`): the
  frontend intersects the view ray with the quadric in the fragment shader, with
  a bounding-box proxy that writes `gl_FragDepth`.
- **Conic/curve entities** (`Ellipse`, `Hyperbola`, `Parabola`, `LinePair`,
  `PlaneConic`, `PlaneConicPair`, `Curve`, …) are **sampled** on the Python side
  into ordered polylines (one per connected component) and streamed to per-kind
  renderers (`curve.js`, `plane_pair.js`, 2D conic renderers).  Unbounded
  conics are clipped to a spatial `extent`.

A raw MV blade can be passed straight to `viz.new` / `viz.add` (the visualizer
analyzes it), so the join from above renders directly.  To draw an arbitrary
quadric from coefficients, build the matrix and wrap it:

```python
from pytanga.geometry import Quadric3D
from pytanga.quadric import to_coeffs

viz.add(Quadric3D(to_coeffs(matrix)), color="#44aaff")
```

## Examples

- `py/examples/ga/quadric/conic_demo.py` — conic through 5 points, rotated by a slider
- `py/examples/ga/quadric/quadric3d_demo.py` — quadric through 9 points, rotated by sliders
- `py/examples/ga/quadric/general_quadric.py` — hyperboloid/cone/paraboloid from coefficients
