# Creation Pipeline — Geometry → MV

The creation pipeline constructs multivectors from geometric entity/operator
dataclasses. It is the inverse of the [analysis pipeline](analysis.md).

The recommended API is a bound [`Geometry`](_geometry.py) instance:

```python
from pytanga.geometry import Geometry
```

## `geo.create(obj) → MV`

Convenience method that accepts either an `Entity` or `Operator` and
constructs the corresponding MV.

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Geometry, Point, Rotor, Direction
import math

e3 = BasisE3()
pga = BasisPGA3()

geom_e3 = Geometry(e3)
geom_pga = Geometry(pga)

# Create a point in E3
mv = geom_e3.create(Point(1, 2, 3))
print(mv)  # 1 e1 + 2 e2 + 3 e3

# Create a rotor in PGA3
r = Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1))
mv = geom_pga.create(r)
```

## OPNS / IPNS

The default `Geometry(algebra)` uses OPNS.  To switch to IPNS, pass `opns=False`
at construction time, or override per call:

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Geometry, Point

n3 = BasisN3()

# Default OPNS (recommended for most uses)
geo = Geometry(n3, opns=True)
mv = geo.create(Point(1, 0, 0))         # OPNS point

# Override to IPNS for a single call
mv_ipns = geo.create(Point(1, 0, 0), opns=False)

# Or create an IPNS-bound instance
geom_ipns = Geometry(n3, opns=False)
mv = geom_ipns.create(Point(1, 0, 0))    # IPNS point
```

## Plain Functions

The underlying plain functions are available directly.  They require the
algebra and OPNS flag to be passed explicitly:

```python
from pytanga.geometry import create, create_entity, create_operator

mv = create(algebra, obj, opns=True)            # Entity or Operator
mv = create_entity(algebra, entity, opns=True)  # Entity only
mv = create_operator(algebra, operator)          # Operator only
```

## Algebra-Specific Entity Representations

| Entity | E3 | P3 | PGA3 | N3 |
|--------|----|----|------|----|
| Point | `x·e1 + y·e2 + z·e3` | `x·e1 + y·e2 + z·e3 + e4` | IPNS: `x·e1 + y·e2 + z·e3 + e₀` (OPNS: grade‑3 trivector) | Conformal: `0.5(r²-1)ep + 0.5(r²+1)em` |
| Direction | Same as Point | `x·e1 + y·e2 + z·e3` | `x·e1 + y·e2 + z·e3` (no e₀ component) | `x·e1 + y·e2 + z·e3` |
| Line | — | `origin ∧ direction` | OPNS: Intersection of 2 planes (grade 2, Gunn/Dorst) | IPNS: 2 points ∧ e∞ |
| Plane | Bivector | 3 points on plane | OPNS: `n + d·e₀` (grade 1, Gunn/Dorst) | IPNS: 3 points ∧ e∞ |
| Circle | — | — | — | IPNS: sphere ∩ plane |
| Sphere | — | — | — | IPNS: `c - 0.5·r²·e∞` |
| PointPair | — | — | — | IPNS: `p1_c ∧ p2_c` |
| Space | `e123` | `e1234` | `e1∧e2∧e3∧e₀` (grade 4) | `I` |

## Unsupported Entity/Operator Types

Calling `create()` with an entity/operator not supported in the detected
algebra raises `TypeError`:

- **E3:** `Circle`, `Sphere`, `PointPair`, `Translator`, `Motor`, `Dilator` → `TypeError`
- **P3:** `Circle`, `Sphere`, `PointPair`, `Translator`, `Motor`, `Dilator` → `TypeError`
- **PGA3:** `PointPair`, `Circle`, `Sphere`, `Inversion`, `Dilator`, `GeneralDilator` → `TypeError`
- **N3:** All types supported (except `GeneralDilator`/`GeneralRotor` which raise `TypeError` for now)