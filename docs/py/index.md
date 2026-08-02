# pytanga User Documentation

This section describes the public Python API of **pytanga** — the Python
interface to TanGA's geometric algebra engine.

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Environment & Setup](env/index.md) | Installation prerequisites, uv environment, automatic C++ compilation and caching |
| [Algebra submodule](algebra/index.md) | `Algebra`, `MV`, duals, modulus arithmetic — the core GA types and operations |
| [Basis classes](basis/index.md) | How `BasisE3`, `BasisP3`, `BasisN3`, `BasisPGA3` expose named blades and factory methods |
| [BladeMask](blade-mask/index.md) | Construction, properties, set operations — the foundational type labelling all matrix and tensor axes |
| [Matrix Operations](matrix/index.md) | `MVMatrix`, `MVProductMatrix` — product‑matrix and blade‑mask pipeline |
| [Equation Solving](solver/index.md) | `solve`, `solve_lsq`, `solve_mod` — automatic blade‑mask derivation and linear system solving via free functions |
| [Tensor Operations](tensors/index.md) | `MVTensor`, `MVLabeledTensor`, `product_tensor()` — label‑driven tensor contractions, broadcasts, and slicing |
| [Geometry Submodule](geometry/index.md) | `Point`, `Line`, `Plane`, `Rotor`, `Motor` — algebra-independent entity/operator types, `analyze()` and `create()` pipelines |
| [3D Visualizer](viz/index.md) | Interactive Three.js visualization in the browser — add entities, apply styles, animate, export to HTML/glTF/MP4 |

## Quick Start

```python
import pytanga

# Euclidean 3D algebra
alg = pytanga.Algebra(3, 0)

# Create multivectors
a = alg("e1 + 2 e2")
b = alg("e2 + e3")

# Geometric product
print(a * b)

# Outer product
print(a ^ b)
```

For named blades and convenience factory methods use a `Basis` class:

```python
from pytanga.basis import BasisE3

E3 = BasisE3()
v  = E3.vector(1, 2, 3)
w  = E3.vector(0, 1, 0)
print(v * w)
```

## AI-Tool Documentation Access

When pytanga is installed as a dependency, the markdown documentation is
packaged with the wheel. AI coding tools can make the docs available via:

```python
import pytanga
pytanga.install_docs()
```

This creates a symlink at `.dep-docs/pytanga/` in the current repository
root, pointing to the packaged `_docs/` directory (or the local `docs/`
in a source checkout). AI tools can then read e.g.
`.dep-docs/pytanga/py/geometry/entities.md` without needing the full
tanga source.

The function is idempotent — call it again to repair a broken symlink.

## Example Scripts

All examples live under `py/examples/` and can be run with:

```
uv run python py/examples/<script>.py
```

| Script | Topic |
|--------|-------|
| [`binding_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/binding_demo.py) | Cache, code-generation and compilation pipeline |
| [`algebra_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/algebra_demo.py) | `Algebra` construction, dimensions, signatures, dtypes |
| [`mv_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/mv_demo.py) | `MV` operators, coefficient access, utility methods |
| [`basis_usage.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/basis_usage.py) | Three patterns for accessing named basis blades |
| [`base_e3_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/base_e3_demo.py) | `BasisE3` — Euclidean 3D |
| [`base_p3_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/base_p3_demo.py) | `BasisP3` — Projective 3D |
| [`base_n3_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/base_n3_demo.py) | `BasisN3` — Null / conformal 3D |
| [`base_pga3_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/base_pga3_demo.py) | `BasisPGA3` — PGA 3D with geometric factory methods |
| [`modulus_algebra_single.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/modulus_algebra_single.py) | Integer algebra with a fixed modulus |
| [`modulus_algebra_multi.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/modulus_algebra_multi.py) | Two different moduli on the same algebra (NTRU style) |
| [`geometry/e3_entities.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/geometry/e3_entities.py) | E3 Point, Plane, Reflection, Rotor — create, analyze, IPNS |
| [`geometry/p3_entities.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/geometry/p3_entities.py) | P3 Point, Direction, Line, Plane — homogeneous, IPNS |
| [`geometry/pga3_entities.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/geometry/pga3_entities.py) | PGA3 Translator, Motor — single null vector |
| [`geometry/n3_entities.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/geometry/n3_entities.py) | N3 entities: Point, Circle, Sphere, Plane — IPNS, grade distinction |
| [`geometry/n3_operators.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/geometry/n3_operators.py) | N3 operators: Rotor, Motor, Inversion, Dilator — entity/operator duality |

## Background

For the mathematical background of the null-vector embedding used in
`BasisN3` and `BasisPGA3`, see
[pga_null_embedding.md](basis/pga_null_embedding.md).
