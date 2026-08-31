# Basis Classes

The `pytanga.basis` submodule provides eight **Basis** subclasses of
`Algebra` that expose all named basis blades as attributes.  Four are for
3D geometry and four for 2D.  They are the recommended starting point for
interactive work, scripts, and notebooks.

Among the 3D classes, [`BasisE3`](bases.md#basise3-euclidean-3d-g3-0) covers
Euclidean 3D, [`BasisP3`](bases.md#basisp3-projective-3d-g4-0) covers Projective 3D,
[`BasisN3`](bases.md#basisn3-nullconformal-3d-g5-0textb10000) covers
conformal/null 3D using the [null‑vector embedding](pga_null_embedding.md),
and [`BasisPGA3`](bases.md#basispga3-pga-3d) implements the Gunn/Dorst
plane‑based PGA.

Among the 2D classes, [`BasisE2`](bases.md#basise2-euclidean-2d-g2-0) covers
Euclidean 2D, [`BasisP2`](bases.md#basisp2-projective-2d-g3-0) covers
Projective 2D with homogeneous coordinates,
[`BasisN2`](bases.md#basisn2-nullconformal-2d-g4-0textb1000) covers
conformal/null 2D, and [`BasisPGA2`](bases.md#basispga2-pga-2d) implements
the Gunn/Dorst plane‑based PGA for 2D Euclidean geometry.

The [Bases](bases.md) page also describes three patterns for accessing named
blades: explicit assignment, attribute access, and namespace injection.

```python
from pytanga.basis import BasisE2, BasisP2, BasisN2, BasisPGA2
from pytanga.basis import BasisE3, BasisP3, BasisN3, BasisPGA3
```

## Reference

| Topic | Guide |
|-------|-------|
| All eight basis classes — `BasisE2`/`P2`/`N2`/`PGA2` and `BasisE3`/`P3`/`N3`/`PGA3` | [Bases](bases.md) |
| Null‑vector embedding — mathematical foundation for `BasisN3`, `BasisPGA3`, `BasisN2`, and `BasisPGA2` | [Null‑Vector Embedding](pga_null_embedding.md) |
| Per‑class detail pages | [BasisE2](basis_e2.md), [BasisP2](basis_p2.md), [BasisN2](basis_n2.md), [BasisPGA2](basis_pga2.md) |

## Quick start

```python
from pytanga.basis import BasisE3

E3 = BasisE3()

# Named blades as attributes; multivectors from strings
v = E3("e1 + 2 e2 + 3 e3")
b = E3.e1 * E3.e2           # geometric product → e12

E3.show(v, "v")
print(b)                     # "e12"
```
