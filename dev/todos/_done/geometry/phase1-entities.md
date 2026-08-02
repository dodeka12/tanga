# Phase 1: Geometric Entity Data Classes

**File:** `py/pytanga/geometry/entities.py`

**Goal:** Define algebra-independent `@dataclass` classes for all geometric entities that
can be represented in TANGA's supported algebras (E3, P3, N3/PGA3). These classes
serve as the input/output type for entity decomposition/analysis and entity construction.

---

## 1. Design Decisions

### 1.1 Data Classes with No Algebra Dependency

```python
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class Point:
    x: float
    y: float
    z: float
```

These classes are pure data containers. They:
- Hold Euclidean 3D coordinates (and optionally additional parameters like radius).
- Have **no** dependency on `pytanga.algebra`, `pytanga.MV`, or `pytanga.basis.*`.
- Can be constructed directly from Python scalars.
- Can be serialized/printed trivially.

### 1.2 Coordinate Convention

All coordinates are in **Euclidean 3D space** (x, y, z). Even when the underlying
algebra uses different representations:
- **E3:** x, y, z directly map to e1, e2, e3 coefficients.
- **P3:** x, y, z map to e1, e2, e3 with homogeneous weight in e4 (1 for finite points, 0 for directions).
- **N3/PGA3:** x, y, z map to e1, e2, e3 with appropriate ei, eo coefficients.

The algebra-specific analysis modules handle the conversion between MV coefficient
space and Euclidean coordinate space.

### 1.3 Naming Convention

Entity class names follow the Perwass book convention:
- `Point` — a single point in 3D space
- `PointPair` — a pair of points (CGA)
- `Direction` — an ideal point / direction at infinity
- `Line` — a line in 3D space
- `Plane` — a plane in 3D space
- `Circle` — a circle in 3D space (CGA)
- `Sphere` — a sphere in 3D space (CGA)
- `Space` — the entire 3D volume

---

## 2. Entity Class Specifications

### 2.1 `Point`

A finite Euclidean 3D point.

```python
@dataclass(frozen=True)
class Point:
    x: float
    y: float
    z: float
```

**Algebra support:** E3, P3, N3/PGA3

**E3 MV:** `x·e1 + y·e2 + z·e3` (grade 1 vector)
**P3 MV:** `x·e1 + y·e2 + z·e3 + 1·e4` (grade 1, homogeneous)
**N3/PGA3 MV:** `x·e1 + y·e2 + z·e3 + 0.5·(x²+y²+z²-1)·ep + 0.5·(x²+y²+z²+1)·em` (grade 1, conformal)

### 2.2 `Direction`

An ideal point / direction at infinity (has no finite position).

```python
@dataclass(frozen=True)
class Direction:
    x: float
    y: float
    z: float
```

**Algebra support:** P3, N3/PGA3 (not E3)

**P3 MV:** `x·e1 + y·e2 + z·e3 + 0·e4` (homogeneous, e4 component is zero)
**N3/PGA3 MV:** `x·e1 + y·e2 + z·e3 + α·einf` (pure einfi component, null)

Note: In E3 there is no distinction between a point and a direction — both are just
grade-1 vectors. The `Direction` type is not used with E3.

### 2.3 `PointPair`

A pair of points in CGA (represented as a grade-2 blade in N3).

```python
@dataclass(frozen=True)
class PointPair:
    point_a: Point
    point_b: Point
```

**Algebra support:** N3/PGA3 only

Alternatively, could be represented by a `Point` center and a direction vector plus
distance. If a point pair degenerates to a single point (tangent), `point_a == point_b`.

### 2.4 `Line`

An infinite line in 3D space.

```python
@dataclass(frozen=True)
class Line:
    origin: Point       # closest point on line to origin, or any point on the line
    direction: Direction  # normalized direction vector
```

**Algebra support:** P3, N3/PGA3

**P3 MV:** `origin ∧ direction = (e1,e2,e3,e4) ∧ (e1,e2,e3,0)` → grade-2 blade
**N3/PGA3 MV:** grade-3 blade in the conformal model

Lines at infinity have `direction` with zero length — the `origin` field then holds the
normal vector of the two parallel planes whose intersection is the line at infinity.

### 2.5 `Plane`

An infinite plane in 3D space.

```python
@dataclass(frozen=True)
class Plane:
    point: Point       # any point on the plane (e.g. closest to origin)
    normal: Direction   # unit normal vector
```

**Algebra support:** E3, P3, N3/PGA3

**E3 MV:** A plane through the origin is a pure bivector:
  `nx·e23 + ny·e31 + nz·e12` where (nx, ny, nz) is the plane normal.
  For offset planes, the IPNS representation `n + d·I` (where I = e123)
  is used, dualizing to a bivector-plus-pseudoscalar combination.
  In all cases, the `(point, normal)` entity representation captures
  the full geometric meaning.

**P3 MV:** grade-3 blade (trivector) in IPNS: `p1 ∧ p2 ∧ p3` where p1,p2,p3 are
          three points on the plane.

**N3/PGA3 MV:** grade-4 blade in IPNS: `p1 ∧ p2 ∧ p3 ∧ einf` where p1,p2,p3 are
               three points on the plane, or `n + d·einf` in dual form.

### 2.6 `Circle`

A circle in 3D space (CGA only).

```python
@dataclass(frozen=True)
class Circle:
    center: Point
    normal: Direction   # plane normal (axis of circle)
    radius: float
```

**Algebra support:** N3/PGA3 only

**N3/PGA3 MV:** grade-3 blade, intersection of a sphere and a plane.

### 2.7 `Sphere`

A sphere in 3D space (CGA only).

```python
@dataclass(frozen=True)
class Sphere:
    center: Point
    radius: float
```

**Algebra support:** N3/PGA3 only

**N3/PGA3 MV:** grade-4 blade in IPNS. A sphere with center c and radius r is
               represented as `c - 0.5·r²·einf` in the conformal model.

### 2.8 `Space`

The entire 3D volume / pseudoscalar.

```python
@dataclass(frozen=True)
class Space:
    pass  # no parameters — just the volume element
```

**Algebra support:** E3, P3, N3/PGA3

The pseudoscalar I. No parameters needed.

---

## 3. Optional / Extended Entity Classes

These are lower-priority but may be useful:

### 3.1 `FlatPoint` (P3 only)

A point in P3 that carries the homogeneous weight. Equivalent to `Point` but
with an explicit weight:

```python
@dataclass(frozen=True)
class FlatPoint:
    x: float
    y: float
    z: float
    weight: float = 1.0  # e4 coefficient. 0 = direction at infinity
```

This could be exposed as a separate entity or folded into `Point` with an optional
`weight` field. Decision: keep `Point` simple and provide algebra-specific helpers
for homogeneous weighting.

### 3.2 `Tangent` / `Flat` variants (N3/PGA3)

CGA can represent tangent vectors, flat points, etc. These are advanced use cases
and can be added in a later iteration.

---

## 4. Complete `entities.py` Structure

```python
# py/pytanga/geometry/entities.py

"""Algebra-independent geometric entity data classes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    """A finite point in Euclidean 3D space."""
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class Direction:
    """A direction vector in 3D space (ideal point at infinity)."""
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class PointPair:
    """A pair of points (CGA grade-2 entity)."""
    point_a: Point
    point_b: Point


@dataclass(frozen=True)
class Line:
    """An infinite line in 3D space."""
    origin: Point       # a point on the line
    direction: Direction  # normalized direction


@dataclass(frozen=True)
class Plane:
    """An infinite plane in 3D space."""
    point: Point        # a point on the plane
    normal: Direction    # unit normal vector


@dataclass(frozen=True)
class Circle:
    """A circle in 3D space (CGA/PGA only)."""
    center: Point
    normal: Direction    # plane normal / axis of the circle
    radius: float


@dataclass(frozen=True)
class Sphere:
    """A sphere in 3D space (CGA/PGA only)."""
    center: Point
    radius: float


@dataclass(frozen=True)
class Space:
    """The entire 3D volume (pseudoscalar)."""
    pass


# Union type for all entities
Entity = Point | Direction | PointPair | Line | Plane | Circle | Sphere | Space
```

## 5. Implementation Steps

1. Create `py/pytanga/geometry/` directory.
2. Create `py/pytanga/geometry/__init__.py` — re-export all entity classes.
3. Create `py/pytanga/geometry/entities.py` with the classes listed above.
4. Update `py/pytanga/__init__.py` — add `from .geometry import ...` or
   keep geometry as an explicit sub-import (`from pytanga.geometry import Point, Line, ...`).

## 6. Verification Checklist

- [ ] All entity classes are `@dataclass(frozen=True)` for immutability.
- [ ] No imports from `pytanga.algebra`, `pytanga.MV`, or `pytanga.basis`.
- [ ] Each class is documented with a docstring.
- [ ] The `Entity` union type covers all entities.
- [ ] `py/pytanga/geometry/__init__.py` re-exports all entity classes.