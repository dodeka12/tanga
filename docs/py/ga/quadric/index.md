# Quadrics

`pytanga.quadric` represents **2D conics** (symmetric 3×3 matrices) and **3D
quadrics** (symmetric 4×4 matrices) as grade-1 blades of a Euclidean-rescaled
projective quadric space.  Points embed as rank-1 matrices, conics/quadrics are
reconstructed as joins of those embeddings, and the results are analysed back
into concrete entities and rendered in the viewer.

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Bases (Q2/Q3)](bases.md) | `BasisQ2` (conic space `CA{6}`) and `BasisQ3` (quadric space `CA{10}`) — blades, the Euclidean rescaling, point embedding |
| [Conic space & visualization](conic-space.md) | Reconstructing conics/quadrics from points, `analyze`/`refine`, the rotation rotor, and how they render |
| [Point tuples (7→8)](point-tuples.md) | Point joins and their dual nets, and the Cayley–Bacharach 7→8 point effect |

## Quick start

```python
from pytanga.geometry import Geometry, Point
from pytanga.quadric import BasisQ3

Q3 = BasisQ3(opns=True)
geo = Geometry(Q3)

# Nine points on a quadric; the join of their embeddings is the quadric.
p1 = geo(Point(2.0, 0.0, 0.0))
# … eight more …
quadric = p1 ^ p2 ^ p3 ^ p4 ^ p5 ^ p6 ^ p7 ^ p8 ^ p9   # grade-9 OPNS blade

viz.new(quadric)   # the visualizer analyzes the MV and draws the quadric
```

## Examples

- `py/examples/ga/quadric/conic_demo.py` — conic through 5 points, rotated by a slider
- `py/examples/ga/quadric/quadric3d_demo.py` — quadric through 9 points, rotated by sliders
- `py/examples/ga/quadric/general_quadric.py` — arbitrary quadrics from coefficients
- `py/examples/ga/quadric/point_tuples_demo.py`, `plane_pair_demo.py`,
  `quadric3d_raycast.py`, `quadric_intersection_demo.py`

## Background

The mathematical derivation lives in the developer docs:
[Conic & quadric space](../../../dev/ga/conic-quadric-space.md) and
`dev/theory/quadric-{rotor,point-tuples,plane-pair}-derivation.md`.
