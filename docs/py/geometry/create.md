# Creation Pipeline — Geometry → MV

The creation pipeline constructs multivectors from geometric entity/operator
dataclasses. It is the inverse of the [analysis pipeline](analysis.md).

```python

from pytanga.geometry import create, create_entity, create_operator
```

## `create(basis, obj) → MV`

Convenience function that accepts either an `Entity` or `Operator` and
dispatches accordingly.

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Point, Rotor, Direction, create
import math

e3 = Algebra.from_name('E3')
pga = Algebra.from_name('PGA3')

# Create a point in E3
mv = create(e3, Point(1, 2, 3))
print(mv)  # 1 e1 + 2 e2 + 3 e3

# Create a rotor in PGA3
r = Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1))
mv = create(pga, r)
```

## `create_entity(basis, entity) → MV`

Creates an MV from an `Entity` dataclass. The algebra determines the
representation:

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Point, create_entity

e3 = Algebra.from_name('E3')
pga = Algebra.from_name('PGA3')

# Same point, different MVs in different algebras
mv_e3 = create_entity(e3, Point(1, 2, 3))
mv_pga = create_entity(pga, Point(1, 2, 3))
```

## `create_operator(basis, operator) → MV`

Creates an MV from an `Operator` dataclass:

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Translator, Direction, create_operator

pga = Algebra.from_name('PGA3')
t = Translator(vector=Direction(1, 0, 0))
mv = create_operator(pga, t)
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