# Phase 8: Entity/Operator Creation (MV Construction)

**Files:**
- `py/pytanga/geometry/create.py` — top-level creation dispatcher
- `py/pytanga/geometry/create_e3.py` — E3-specific creation
- `py/pytanga/geometry/create_p3.py` — P3-specific creation
- `py/pytanga/geometry/create_pga3.py` — PGA3-specific creation
- `py/pytanga/geometry/create_n3.py` — N3-specific creation

**Goal:** Implement the inverse pipeline of analysis: given an algebra basis and a
geometric entity/operator dataclass, construct the corresponding multivector. This
is a clean, algebra-independent factory API.

---

## 1. Architecture

```
                      ┌──────────────────┐
                      │   create.py      │
                      │ create_entity()  │ ← single entry point
                      │ create_operator()│
                      └────────┬─────────┘
                               │
               Determine algebra type (E3 / P3 / PGA3 / N3)
               by inspecting the basis class
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
    ┌────────────────┐ ┌──────────────┐ ┌──────────────────┐
    │  create_e3.py   │ │ create_p3.py │ │  create_pga3.py   │
    │                 │ │              │ │                  │
    │ create_point()  │ │create_point()│ │ create_point()    │
    │ create_plane()  │ │create_line() │ │ create_line()     │
    │ create_rotor()  │ │create_plane()│ │ create_plane()    │
    └────────────────┘ │create_rotor()│ │ create_rotor()    │
                        └──────────────┘ │ create_translator()│
                                         │ create_motor()    │
                                         └──────────────────┘
                                              │
                                         ┌────┴────────────┐
                                         │  create_n3.py    │
                                         │                  │
                                         │ create_point()   │
                                         │ create_line()    │
                                         │ create_circle()  │
                                         │ create_plane()   │
                                         │ create_sphere()  │
                                         │ create_rotor()   │
                                         │ create_translator()│
                                         │ create_dilator() │
                                         │ create_motor()   │
                                         └──────────────────┘
```

---

## 2. Design Principles

### 2.1 Same Dispatcher Pattern as `analysis.py`

The `create.py` dispatcher follows the `analysis.py` pattern:

```python
from pytanga.basis.e3 import BasisE3
from pytanga.basis.p3 import BasisP3
from pytanga.basis.n3 import BasisN3
from pytanga.basis.pga3 import BasisPGA3

def _detect(basis) -> str:
    if isinstance(basis, BasisPGA3):
        return "pga3"
    elif isinstance(basis, BasisN3):
        return "n3"
    elif isinstance(basis, BasisP3):
        return "p3"
    elif isinstance(basis, BasisE3):
        return "e3"
    else:
        raise ValueError(f"Unknown basis type: {type(basis)}")
```

### 2.2 `create_entity()` — Single Dispatcher

```python
def create_entity(basis, entity: Entity) -> MV:
    """Create an MV from a geometric entity dataclass.

    Args:
        basis: An algebra basis instance (BasisE3, BasisP3, BasisPGA3, BasisN3).
        entity: An Entity dataclass (Point, Line, Plane, Circle, Sphere, etc.).

    Returns:
        An MV representing the entity in the given algebra.

    Raises:
        TypeError: If the entity type is not supported in the given algebra.
    """
    alg_type = _detect(basis)

    if alg_type == "e3":
        return _create_entity_e3(basis, entity)
    elif alg_type == "p3":
        return _create_entity_p3(basis, entity)
    elif alg_type == "pga3":
        return _create_entity_pga3(basis, entity)
    elif alg_type == "n3":
        return _create_entity_n3(basis, entity)


def _create_entity_e3(basis, entity: Entity) -> MV:
    from . import create_e3
    if isinstance(entity, Point):
        return create_e3.create_point(basis, entity.x, entity.y, entity.z)
    elif isinstance(entity, Plane):
        return create_e3.create_plane(basis, entity.normal, entity.point)
    elif isinstance(entity, Space):
        return create_e3.create_space(basis)
    else:
        raise TypeError(f"Entity {type(entity).__name__} not supported in E3")
```

### 2.3 `create_operator()` — Single Dispatcher

```python
def create_operator(basis, operator: Operator) -> MV:
    """Create an MV from an operator dataclass.

    Args:
        basis: An algebra basis instance.
        operator: An Operator dataclass (Rotor, Translator, Motor, etc.).

    Returns:
        An MV representing the versor in the given algebra.
    """
    alg_type = _detect(basis)
    ...
```

### 2.4 `create()` — Convenience

```python
def create(basis, obj: Entity | Operator) -> MV:
    """Create an MV from either an entity or operator dataclass.

    Dispatches to create_entity() or create_operator() based on the type.
    """
    if isinstance(obj, Entity):
        return create_entity(basis, obj)
    elif isinstance(obj, Operator):
        return create_operator(basis, obj)
    else:
        raise TypeError(f"Expected Entity or Operator, got {type(obj)}")
```

---

## 3. Algebra-Specific Creation Modules

### 3.1 `create_e3.py`

| Function | Parameters | Returns |
|----------|-----------|---------|
| `create_point(basis, x, y, z)` | Euclidean coordinates | `x·e1 + y·e2 + z·e3` |
| `create_plane(basis, normal, point)` | Normal + point on plane | Bivector (origin plane) |
| `create_space(basis)` | — | Pseudoscalar e123 |
| `create_rotor(basis, angle, axis)` | Angle + axis | `cos(θ/2) + sin(θ/2)·B` |
| `create_reflection(basis, normal)` | Normal vector | Grade-1 vector |

### 3.2 `create_p3.py`

| Function | Parameters | Returns |
|----------|-----------|---------|
| `create_point(basis, x, y, z)` | Euclidean coordinates | `x·e1 + y·e2 + z·e3 + e4` |
| `create_direction(basis, x, y, z)` | Direction vector | `x·e1 + y·e2 + z·e3` (no e4) |
| `create_line(basis, origin, direction)` | Origin point + direction | `point ∧ direction` (grade 2) |
| `create_plane(basis, plane)` | Plane dataclass | `p1∧p2∧p3` (grade 3, IPNS) |
| `create_space(basis)` | — | Pseudoscalar e1234 |
| `create_rotor(basis, angle, axis)` | Angle + axis | Same formula as E3 |
| `create_reflection(basis, normal)` | Normal | Grade-1 with homogeneous component |

### 3.3 `create_pga3.py`

| Function | Parameters | Returns |
|----------|-----------|---------|
| `create_point(basis, x, y, z)` | Euclidean coordinates | `x·e1 + y·e2 + z·e3 + einf` |
| `create_direction(basis, x, y, z)` | Direction vector | `x·e1 + y·e2 + z·e3` |
| `create_line(basis, origin, direction)` | Origin + direction | Grade-3 blade (IPNS) |
| `create_plane(basis, plane)` | Plane dataclass | Grade-4 blade (IPNS) |
| `create_space(basis)` | — | Pseudoscalar |
| `create_rotor(basis, angle, axis)` | Angle + axis | Same formula |
| `create_translator(basis, vector)` | Translation vector | `1 - 0.5·t·einf` |
| `create_motor(basis, rotor, translator)` | Rotor + Translator | `T · R` |
| `create_reflection(basis, normal)` | Normal | Grade-1 vector |

### 3.4 `create_n3.py`

Full set including N3-only entities and operators:

| Function | Parameters | Returns |
|----------|-----------|---------|
| `create_point(basis, x, y, z)` | Euclidean coordinates | Full conformal point |
| `create_direction(basis, x, y, z)` | Direction vector | Euclidean vector |
| `create_point_pair(basis, p1, p2)` | Two points | Grade-2 blade (IPNS) |
| `create_line(basis, origin, direction)` | Origin + direction | Grade-3 blade (IPNS) |
| `create_circle(basis, center, normal, radius)` | Center, normal, radius | Grade-3 blade (IPNS) |
| `create_plane(basis, plane)` | Plane dataclass | Grade-4 blade (IPNS) |
| `create_sphere(basis, center, radius)` | Center, radius | Grade-4 blade (IPNS) |
| `create_space(basis)` | — | Pseudoscalar |
| `create_rotor(basis, angle, axis)` | Angle + axis | `cos(θ/2) + sin(θ/2)·B` |
| `create_translator(basis, vector)` | Translation vector | `1 - 0.5·t·einf` |
| `create_dilator(basis, factor)` | Dilation factor | `cosh(γ/2) + sinh(γ/2)·E` |
| `create_motor(basis, rotor, translator)` | Rotor + Translator | `T · R` |
| `create_reflection(basis, normal)` | Normal | Grade-1 (no eo) |
| `create_inversion(basis, origin)` | Origin point | Grade-1 (with eo) |

---

## 4. `create.py` — Full Implementation

```python
# py/pytanga/geometry/create.py

"""Geometry creation dispatcher — MV construction from Entity/Operator dataclasses.

This is the inverse of analysis: create_entity(basis, point) → MV
"""

from __future__ import annotations

from pytanga.algebra._mv import MV
from pytanga.basis.e3 import BasisE3
from pytanga.basis.p3 import BasisP3
from pytanga.basis.n3 import BasisN3
from pytanga.basis.pga3 import BasisPGA3

from .entities import (
    Circle,
    Direction,
    Entity,
    Line,
    Plane,
    Point,
    PointPair,
    Space,
    Sphere,
)
from .operators import (
    Dilator,
    GeneralDilator,
    GeneralRotor,
    Inversion,
    Motor,
    Operator,
    Reflection,
    Rotor,
    Translator,
)


def _detect(basis) -> str:
    """Detect algebra type from basis instance."""
    if isinstance(basis, BasisPGA3):
        return "pga3"
    elif isinstance(basis, BasisN3):
        return "n3"
    elif isinstance(basis, BasisP3):
        return "p3"
    elif isinstance(basis, BasisE3):
        return "e3"
    else:
        raise ValueError(f"Unknown basis type: {type(basis).__name__}")


def create_entity(basis, entity: Entity) -> MV:
    """Create an MV representing a geometric entity."""
    from . import create_e3, create_p3, create_pga3, create_n3

    modules = {
        "e3": create_e3,
        "p3": create_p3,
        "pga3": create_pga3,
        "n3": create_n3,
    }
    mod = modules[_detect(basis)]

    if isinstance(entity, Point):
        return mod.create_point(basis, entity.x, entity.y, entity.z)
    elif isinstance(entity, Direction):
        return mod.create_direction(basis, entity.x, entity.y, entity.z)
    elif isinstance(entity, PointPair):
        return mod.create_point_pair(basis, entity.point_a, entity.point_b)
    elif isinstance(entity, Line):
        return mod.create_line(basis, entity.origin, entity.direction)
    elif isinstance(entity, Circle):
        return mod.create_circle(basis, entity.center, entity.normal, entity.radius)
    elif isinstance(entity, Plane):
        return mod.create_plane(basis, entity)
    elif isinstance(entity, Sphere):
        return mod.create_sphere(basis, entity.center, entity.radius)
    elif isinstance(entity, Space):
        return mod.create_space(basis)
    else:
        raise TypeError(f"Unknown entity type: {type(entity).__name__}")


def create_operator(basis, operator: Operator) -> MV:
    """Create an MV representing a versor/operator."""
    from . import create_e3, create_p3, create_pga3, create_n3

    modules = {
        "e3": create_e3,
        "p3": create_p3,
        "pga3": create_pga3,
        "n3": create_n3,
    }
    mod = modules[_detect(basis)]

    if isinstance(operator, Reflection):
        return mod.create_reflection(basis, operator.normal)
    elif isinstance(operator, Inversion):
        return mod.create_inversion(basis, operator.origin)
    elif isinstance(operator, Rotor):
        return mod.create_rotor(basis, operator.angle, operator.axis)
    elif isinstance(operator, Translator):
        return mod.create_translator(
            basis, operator.vector.x, operator.vector.y, operator.vector.z
        )
    elif isinstance(operator, Dilator):
        return mod.create_dilator(basis, operator.factor)
    elif isinstance(operator, GeneralDilator):
        return mod.create_general_dilator(basis, operator)
    elif isinstance(operator, Motor):
        return mod.create_motor(basis, operator.rotor, operator.translator)
    elif isinstance(operator, GeneralRotor):
        return mod.create_general_rotor(basis, operator.rotor, operator.translator)
    else:
        raise TypeError(f"Unknown operator type: {type(operator).__name__}")


def create(basis, obj: Entity | Operator) -> MV:
    """Create an MV from an entity or operator dataclass.

    This is the inverse of analyze(): create(basis, analyze(mv)) produces
    an MV equivalent to the original (up to normalization).
    """
    if isinstance(obj, Entity):
        return create_entity(basis, obj)
    elif isinstance(obj, Operator):
        return create_operator(basis, obj)
    else:
        raise TypeError(
            f"Expected Entity or Operator, got {type(obj).__name__}"
        )
```

---

## 5. Algebra-Specific Skeleton: `create_e3.py`

```python
# py/pytanga/geometry/create_e3.py

"""E3 entity/operator creation — converts dataclasses to MVs."""

import math

from pytanga.algebra._mv import MV
from pytanga.geometry.entities import Direction, Plane, Point


def create_point(basis, x: float, y: float, z: float) -> MV:
    """x·e1 + y·e2 + z·e3"""
    return basis.multivector({1: x, 2: y, 4: z})


def create_direction(basis, x: float, y: float, z: float) -> MV:
    """x·e1 + y·e2 + z·e3 (same as point in E3)"""
    return create_point(basis, x, y, z)


def create_plane(basis, plane: Plane) -> MV:
    """Bivector: nx·e23 + ny·e31 + nz·e12"""
    return basis.multivector({
        6: plane.normal.x,   # e23
        5: plane.normal.y,   # e31
        3: plane.normal.z,   # e12
    })


def create_space(basis) -> MV:
    """Pseudoscalar e123"""
    return basis.multivector({7: 1.0})


def create_rotor(basis, angle: float, axis: Direction) -> MV:
    """cos(θ/2) + sin(θ/2)·(ax·e23 + ay·e31 + az·e12)"""
    half = angle / 2.0
    return basis.multivector({
        0: math.cos(half),
        6: math.sin(half) * axis.x,   # e23
        5: math.sin(half) * axis.y,   # e31
        3: math.sin(half) * axis.z,   # e12
    })


def create_reflection(basis, normal: Direction) -> MV:
    """Grade-1 vector = reflection in plane with given normal."""
    return create_point(basis, normal.x, normal.y, normal.z)
```

---

## 6. Relationship to Analysis Modules

The `create_*` functions are the **inverse** of the `analyze_*` functions:

```
analyze(mv) → Entity          # analysis.py
create(basis, entity) → MV    # create.py

analyze(create(basis, entity)) ≈ entity   # round-trip
```

The analysis modules already contain `make_*` factory functions (e.g.,
`analysis_e3.make_point()`). These can be re-exported or refactored to
use the `create_e3` functions as their underlying implementation, avoiding
duplication. During implementation, the `make_*` functions in the analysis
modules should delegate to the corresponding `create_*` functions.

---

## 7. Implementation Steps

1. Create `py/pytanga/geometry/create.py` — dispatcher with `_detect()`, `create_entity()`, `create_operator()`, `create()`.
2. Create `py/pytanga/geometry/create_e3.py` — E3 entity/operator creation.
3. Create `py/pytanga/geometry/create_p3.py` — P3 entity/operator creation.
4. Create `py/pytanga/geometry/create_pga3.py` — PGA3 entity/operator creation.
5. Create `py/pytanga/geometry/create_n3.py` — N3 entity/operator creation (full set).
6. Update `py/pytanga/geometry/__init__.py` — export `create_entity`, `create_operator`, `create`.
7. Refactor `analysis_*.py` → `make_*()` functions to delegate to `create_*.py` functions.

---

## 8. Not in Scope (PGA3/N3 Limitations)

When `create_entity()` or `create_operator()` is called with an entity/operator
not supported in the detected algebra:
- E3: Calling with Circle/Sphere/PointPair → `TypeError`
- E3: Calling with Translator/Motor → `TypeError`
- P3: Calling with Circle/Sphere/PointPair → `TypeError`
- P3: Calling with Translator/Motor → `TypeError`
- PGA3: Calling with PointPair/Circle/Sphere → `TypeError`
- PGA3: Calling with Inversion/Dilator/GeneralDilator/GeneralRotor → `TypeError`

The `create.py` dispatcher handles this naturally via the `isinstance` chain:
if no matching branch exists, it falls through to the base `TypeError`.

## 9. Verification Checklist

- [ ] `create(basis_e3, Point(1,2,3))` produces a valid E3 point MV
- [ ] `create(basis_e3, Rotor(math.pi/2, Direction(0,0,1)))` produces a valid rotor
- [ ] `create(basis_p3, Line(origin, direction))` produces a valid P3 line
- [ ] `create(basis_pga3, Motor(rotor, translator))` produces a valid PGA3 motor
- [ ] `create(basis_n3, Sphere(center, radius))` produces a valid N3 sphere
- [ ] Round-trip: `analyze(create(basis, entity))` returns equivalent entity
- [ ] Unsupported entity/operator raises `TypeError` with clear message