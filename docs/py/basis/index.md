# Basis Classes

The `pytanga.basis` submodule provides four **Basis** subclasses of
`Algebra` that expose all named basis blades as attributes.  They are the
recommended starting point for interactive work, scripts, and notebooks.
[`BasisE3`](bases.md#basise3--euclidean-3d-g3-0) covers Euclidean 3D,
[`BasisP3`](bases.md#basisp3--projective-3d-g4-0) covers Projective 3D,
[`BasisN3`](bases.md#basisn3--nullconformal-3d-g5-0textb10000) covers
conformal/null 3D using the [null‑vector embedding](pga_null_embedding.md),
and [`BasisPGA3`](bases.md#basispga3--pga-3d) extends `BasisN3` with
geometric factory methods for points and vectors.  The
[Bases](bases.md) page also describes three patterns for accessing named
blades: explicit assignment, attribute access, and namespace injection.

```python
from pytanga.basis import BasisE3, BasisP3, BasisN3, BasisPGA3
```

## Reference

| Topic | Guide |
|-------|-------|
| All four basis classes — `BasisE3`, `BasisP3`, `BasisN3`, `BasisPGA3` | [Bases](bases.md) |
| Null‑vector embedding — mathematical foundation for `BasisN3` and `BasisPGA3` | [Null‑Vector Embedding](pga_null_embedding.md) |

## Quick start

```python
from pytanga.basis import BasisE3

E3 = BasisE3()

# Named blades as attributes
v = E3.vector(1, 2, 3)
b = E3.e1 * E3.e2           # geometric product → e12

E3.show(v, "v")
print(b)                     # "e12"