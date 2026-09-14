# Bases (Q2/Q3)

`pytanga.quadric` linearises conics and quadrics by putting them in a
**projective quadric space** — a geometric algebra whose vectors are the
symmetric-matrix coefficients of a degree-2 hypersurface.  Two bases are
provided:

| Basis | Space | Algebra | Blades | Represents |
|-------|-------|---------|--------|------------|
| `BasisQ2` | conic space `CA{6}` | `Algebra(6, 0)` | `b1 … b6` | 2D conics (symmetric 3×3) |
| `BasisQ3` | quadric space `CA{10}` | `Algebra(10, 0)` | `b1 … b10` | 3D quadrics (symmetric 4×4) |

```python
from pytanga.quadric import BasisQ2, BasisQ3

Q2 = BasisQ2()           # 2D conic space
Q3 = BasisQ3(opns=True)  # 3D quadric space (OPNS convention)
```

The dimension (6 or 10) is exactly the number of independent symmetric-matrix
entries.  `opns=` selects the outer-product (OPNS) convention (default `True`);
pass `opns=False` for the inner-product (IPNS) convention.

## Blade ↔ monomial correspondence

The named blades `b1…bN` correspond to the monomials of the quadratic form.
`BasisQ2.__init__` also sets `b1`…`b6` and `I` (the pseudoscalar) as attributes
(`BasisQ3` sets `b1`…`b10` and `I`):

| blade | Q2 (conic) | Q3 (quadric) |
|---|---|---|
| `b1`, `b2` | x, y | x, y |
| `b3` | 1 (constant) | z |
| `b4` | x² | 1 (constant) |
| `b5` | y² | x² |
| `b6` | xy | y² |
| `b7` | — | z² |
| `b8` | — | xy |
| `b9` | — | xz |
| `b10` | — | yz |

Blade bitmask IDs are powers of two: `b1=1, b2=2, b3=4, …`.

## Euclidean rescaling

Perwass's original conic space uses a **non-Euclidean** basis `e1…e6` with
squared norms `(1, 1, 2, 2, 2, 1)` (Q2) and `(1, 1, 1, 2, 2, 2, 2, 1, 1, 1)`
(Q3).  `pytanga.quadric` rescales to a **Euclidean** basis `b_i` (`b_i·b_i = 1`)
via `b = e/√2` on the norm-2 blades, so the plain `Algebra(6,0)` /
`Algebra(10,0)` metric can be used unchanged.  The `√2/2` factors that the
rescaling introduces appear **only** in the point embedding and the
matrix↔coefficient mapping — every other operation works with `b1…bN`.

## Using a basis with `Geometry`

```python
from pytanga.geometry import Geometry, Point

Q2 = BasisQ2()
geo = Geometry(Q2)

p = geo(Point(1.0, 2.0, 0.0))   # an embedded point (grade-1 blade)
```

`Geometry(basis)` wires the basis into the entity ↔ MV pipelines, so
`geo(Point(...))`, `geo(Rotor(...))`, `geo.analyze(mv)`, and `geo.refine(...)`
all understand the quadric space.

## See Also

- [Conic space & visualization](conic-space.md) — point embedding, reconstruction, rotation, rendering
- [Point tuples (7→8)](point-tuples.md) — joins and the Cayley–Bacharach effect
