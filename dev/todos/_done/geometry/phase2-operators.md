# Phase 2: Operator Data Classes

**File:** `py/pytanga/geometry/operators.py`

**Goal:** Define algebra-independent `@dataclass` classes for all geometric operators
(versors / transformations) that can be represented in TANGA's supported algebras.
These classes serve as the input/output type for operator decomposition/analysis
and operator construction.

---

## 1. Design Decisions

### 1.1 Data Classes with No Algebra Dependency

Same principle as entities: pure data containers with no dependency on
`pytanga.algebra`, `pytanga.MV`, or `pytanga.basis.*`.

### 1.2 Operator Classification

Operators are versors — multivectors that represent orthogonal transformations when
applied via the sandwich product `V · x · rev(V)`. They are grouped into:

- **Grade-1 versors (reflectors):** Reflection, Inversion
- **Even-grade versors (rotors):** Rotation, Translation, Dilation, Motor

### 1.3 Parameter Encoding

Operators are encoded in their natural parameters:

| Operator | Parameters |
|----------|-----------|
| Reflection | Normal vector of the reflection plane |
| Inversion | Inversion origin point (N3 only) |
| Rotor | Rotation axis + angle, or axis + angle |
| Translator | Translation vector |
| Dilator | Dilation factor |
| Motor | Combined rotation + translation |
| General Rotor | Rotor + additional e1i, e2i, e3i bivector components |

---

## 2. Operator Class Specifications

### 2.1 `Reflection`

Reflection in a plane through the origin (grade-1 versor).

```python
@dataclass(frozen=True)
class Reflection:
    """Reflection in a plane through the origin."""
    normal: Direction  # unit normal of the reflection plane (E3/P3)
```

**Algebra support:** E3, P3, N3/PGA3

**E3 MV:** `nx·e1 + ny·e2 + nz·e3` (grade-1 vector, normal to the reflection plane)
**P3 MV:** `nx·e1 + ny·e2 + nz·e3 + nw·e4` (grade-1 with homogeneous component)
**N3/PGA3 MV:** `nx·e1 + ny·e2 + nz·e3 + ni·ei` (grade-1, includes einf component for offset)

In all algebras, reflecting a vector v through a plane with normal n is: `-n · v · n`.

### 2.2 `Inversion`

Inversion in a sphere centered at the origin (N3/PGA3 only).

```python
@dataclass(frozen=True)
class Inversion:
    """Inversion in a sphere centered at the origin."""
    origin: Point   # center of the inversion sphere (typically the origin)
```

**Algebra support:** N3/PGA3 only

**N3/PGA3 MV:** `o` (the grade-1 vector representing the origin's conformal embedding).
               Inversion maps point p to `o · p · o`.

The C++ basis lists both `BasisReflection` and `BasisInversion` masks.
- `BasisReflection`: blades {e1, e2, e3, ei} (does not include eo)
- `BasisInversion`: blades {e1, e2, e3, ei, eo} (includes eo)

An inversion is essentially the grade-1 versor that corresponds to the origin in
conformal space. Drawing a distinction between a pure reflection and an origin
inversion may be subtle — both are grade-1 blades but with different blade composition.

### 2.3 `Rotor`

A 3D rotation (even-grade versor, scalar + bivector).

```python
@dataclass(frozen=True)
class Rotor:
    """A 3D rotation."""
    angle: float           # rotation angle in radians
    axis: Direction        # unit rotation axis vector
```

**Algebra support:** E3, P3, N3/PGA3

**MV:** `cos(θ/2) + sin(θ/2) · (ax·e23 + ay·e31 + az·e12)`

The C++ bases all define the same rotor structure: {scalar, e23, e31, e12}.
The `CreateRotor()` method builds this from axis + angle.

### 2.4 `Translator`

A translation (N3/PGA3 only).

```python
@dataclass(frozen=True)
class Translator:
    """A translation in 3D space."""
    vector: Direction  # translation vector (dx, dy, dz)
```

**Algebra support:** N3/PGA3 only

**N3/PGA3 MV:** `1 - 0.5·(dx·e1i + dy·e2i + dz·e3i)` where e1i = e1∧einf, etc.

The C++ basis shows: `BasisTranslator` = {scalar, e1i, e2i, e3i} (4 blades).
`CreateTranslator()` uses coefficients: {1, -t/2, -t/2, -t/2} × {scalar, e1i, e2i, e3i}
with the blades appearing as {e1∧ei, e2∧ei, e3∧ei} (each appears twice in the
C++ code — once via ep and once via em, since ei = ep+em).

### 2.5 `Dilator`

A global scaling/dilation (N3/PGA3 only).

```python
@dataclass(frozen=True)
class Dilator:
    """A dilation (uniform scaling) about the origin."""
    factor: float  # dilation factor (> 0)
```

**Algebra support:** N3/PGA3 only

**N3/PGA3 MV:** The C++ `BasisDilator` has {scalar, E} where E = einf∧eo.
               A dilator is `cosh(γ/2) + sinh(γ/2)·E` where γ = ln(factor).

### 2.6 `Motor`

A combined rotation + translation (N3/PGA3 only).

```python
@dataclass(frozen=True)
class Motor:
    """A rigid body motion (rotation + translation)."""
    rotor: Rotor
    translator: Translator
```

**Algebra support:** N3/PGA3 only

**N3/PGA3 MV:** `translator_mv · rotor_mv` (or `rotor_mv · translator_mv` depending on convention).
               Basis: {scalar, e23, e31, e12, e1i, e2i, e3i, e123i} (8 blades, 12 with
               degeneracy from ep/em splitting? Actually the C++ has `TBladeListMotor` of
               size 12 and `BasisMotor` with 8 unique blades: {1, e23, e31, e12, e1i, e2i, e3i, e123i}).

### 2.7 `GeneralRotor`

A general even-grade versor in N3/PGA3 (rotor + translator components but without
the e123i "motor" term).

```python
@dataclass(frozen=True)
class GeneralRotor:
    """A general even versor (rotor + translator parts, no motor term)."""
    rotor: Rotor
    translator: Translator
```

**Algebra support:** N3/PGA3 only

**N3/PGA3 MV:** Basis {scalar, e23, e31, e12, e1i, e2i, e3i} (7 blades).
               This is like a motor but without the e123i component.

### 2.8 `GeneralDilator`

A general dilation (with translation-like components).

```python
@dataclass(frozen=True)
class GeneralDilator:
    """A general dilation (scalar + E + translation components)."""
    factor: float
    translator: Translator | None = None
```

**Algebra support:** N3/PGA3 only

**N3/PGA3 MV:** Basis {scalar, e1i, e2i, e3i, E} (5 blades).

---

## 3. Complete `operators.py` Structure

```python
# py/pytanga/geometry/operators.py

"""Algebra-independent operator (versor) data classes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .entities import Direction, Point


@dataclass(frozen=True)
class Reflection:
    """Reflection in a plane through the origin."""
    normal: Direction  # unit normal vector of the reflection plane


@dataclass(frozen=True)
class Inversion:
    """Inversion in a sphere centered at origin (N3/PGA3 only)."""
    origin: Point


@dataclass(frozen=True)
class Rotor:
    """A 3D rotation."""
    angle: float        # rotation angle in radians
    axis: Direction     # unit rotation axis


@dataclass(frozen=True)
class Translator:
    """A translation in 3D space (N3/PGA3 only)."""
    vector: Direction   # translation vector


@dataclass(frozen=True)
class Dilator:
    """A uniform dilation about the origin (N3/PGA3 only)."""
    factor: float       # dilation factor (> 0)


@dataclass(frozen=True)
class Motor:
    """A rigid body motion: rotation + translation (N3/PGA3 only)."""
    rotor: Rotor
    translator: Translator


@dataclass(frozen=True)
class GeneralRotor:
    """A general even versor (N3/PGA3 only)."""
    rotor: Rotor
    translator: Translator


@dataclass(frozen=True)
class GeneralDilator:
    """A general dilation with translation components (N3/PGA3 only)."""
    factor: float
    translator: Optional[Translator] = None


# Union type for all operators
Operator = (
    Reflection
    | Inversion
    | Rotor
    | Translator
    | Dilator
    | Motor
    | GeneralRotor
    | GeneralDilator
)
```

## 4. Implementation Steps

1. Create `py/pytanga/geometry/operators.py` with the classes listed above.
2. Update `py/pytanga/geometry/__init__.py` — re-export all operator classes.

## 5. Verification Checklist

- [ ] All operator classes are `@dataclass(frozen=True)`.
- [ ] No imports from `pytanga.algebra`, `pytanga.MV`, or `pytanga.basis`.
- [ ] Only imports from `.entities` (Direction, Point) — no circular dependencies.
- [ ] The `Operator` union type covers all operators.
- [ ] `__init__.py` re-exports all operator classes.