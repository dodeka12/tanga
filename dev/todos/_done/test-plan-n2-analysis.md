# Test Plan: N2 Entity & Operator Analysis

**Status:** draft  
**Algebra:** `Algebra.from_name("N2")`  
**Implementation file:** `py/tests/geometry/test_geometry_n2_analysis.py`  
**Prerequisite:** Merge `Dilator` + `GeneralDilator` into single `Dilator(factor, origin=Point(0,0,0))` (T·D·T̃ form for general dilator)

Tests for the N2 conformal `create` ↔ `analyze` round-trip and operator application,
following the golden rules:

1. No `abs()` on signed values
2. No `isinstance` unions in expected type
3. Assert all relevant fields
4. Application test is the ultimate validator
5. Tests must fail when the implementation is wrong

---

## 2D Conformal Geometry Notes

In N2 (2D conformal geometry), all entities lie in the XY plane (z=0):
- "Sphere" = circle, "Plane" = line
- Rotations are always about the z-axis (Direction(0,0,1))
- Circle normal is always (0,0,1)
- No ReflectionPlane (lines serve that role)

---

## Boilerplate

```python
from __future__ import annotations
import math
import pytest
from pytanga.algebra._algebra import Algebra
from pytanga.geometry.analysis import analyze_entity, analyze_operator
from pytanga.geometry.create import create_entity, create_operator
from pytanga.geometry.entities import *
from pytanga.geometry.operators import *

@pytest.fixture(scope="module")
def b():
    return Algebra.from_name("N2")
```

---

## 1. Entity Round-Trips (8 tests)

### E1. Point

```python
def test_entity_point_opns_round_trip(b):
    """E1: create Point(3,-2,0) → analyze → assert exact."""
    mv = create_entity(b, Point(3, -2, 0))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(3)
    assert r.y == pytest.approx(-2)
    assert r.z == pytest.approx(0)
```

### E2. Direction

```python
def test_entity_direction_opns_round_trip(b):
    """E2: create Direction(1,2,0) → analyze → assert exact."""
    mv = create_entity(b, Direction(1, 2, 0))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Direction), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(0)
```

### E3. PointPair

The analysis returns `point_a` along −dir from center and `point_b` along +dir.
Verify via midpoint, separation, and direction.

```python
def test_entity_point_pair_opns_round_trip(b):
    """E3: create PointPair → analyze → assert midpoint, separation, direction."""
    a = Point(1, 0, 0)
    b_p = Point(3, 0, 0)
    mv = create_entity(b, PointPair(a, b_p))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, PointPair), f"Got {type(r).__name__}"
    assert not r.is_imaginary
    # Verify midpoint
    mid = Point((a.x + b_p.x) / 2, (a.y + b_p.y) / 2, 0.0)
    r_mid = Point(
        (r.point_a.x + r.point_b.x) / 2,
        (r.point_a.y + r.point_b.y) / 2,
        0.0,
    )
    assert r_mid.x == pytest.approx(mid.x)
    assert r_mid.y == pytest.approx(mid.y)
    # Verify separation
    sep = math.sqrt((b_p.x - a.x)**2 + (b_p.y - a.y)**2)
    r_sep = math.sqrt(
        (r.point_b.x - r.point_a.x)**2
        + (r.point_b.y - r.point_a.y)**2
    )
    assert r_sep == pytest.approx(sep)
    # Verify point_a is along −dir, point_b along +dir
    d = Direction(b_p.x - a.x, b_p.y - a.y, 0.0)
    r_d = Direction(
        r.point_b.x - r.point_a.x,
        r.point_b.y - r.point_a.y,
        0.0,
    )
    assert r_d.x == pytest.approx(d.x)
    assert r_d.y == pytest.approx(d.y)
```

### E4. HPoint

HPoint is `Cop(p)∧e∞` — a grade‑2 OPNS blade containing e∞ as a factor.

```python
def test_entity_hpoint_opns_round_trip(b):
    """E4: create HPoint(Point(2,-1,0), weight=2.5) → analyze → assert."""
    mv = create_entity(b, HPoint(Point(2, -1, 0), weight=2.5))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, HPoint), f"Got {type(r).__name__}"
    assert r.point.x == pytest.approx(2)
    assert r.point.y == pytest.approx(-1)
    assert r.point.z == pytest.approx(0)
    assert r.weight == pytest.approx(2.5)
```

### E5. Line

The analysis returns the closest point to the origin on the line and
normalizes the direction.

```python
def test_entity_line_opns_round_trip(b):
    """E5: create Line(origin=(1,2,0), dir=(1,2,0)) → analyze → assert."""
    direction = Direction(1, 2, 0)
    unit = direction.norm()
    pt = Point(1, 2, 0)
    mv = create_entity(b, Line(pt, direction))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Line), f"Got {type(r).__name__}"
    # Direction normalized and preserves sign
    assert r.direction.x == pytest.approx(unit.x)
    assert r.direction.y == pytest.approx(unit.y)
    assert r.direction.z == pytest.approx(0)
    # Analyzed origin must lie on the line: (r.origin − pt) ∥ direction
    dx = r.origin.x - pt.x
    dy = r.origin.y - pt.y
    cross_z = direction.x * dy - direction.y * dx
    assert cross_z == pytest.approx(0, abs=1e-6)
```

### E6. Circle

```python
def test_entity_circle_opns_round_trip(b):
    """E6: create Circle(center=(1,0,0), normal=(0,0,1), radius=2.5) → analyze."""
    mv = create_entity(b, Circle(Point(1, 0, 0), Direction(0, 0, 1), 2.5))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Circle), f"Got {type(r).__name__}"
    assert not r.is_imaginary
    assert r.center.x == pytest.approx(1)
    assert r.center.y == pytest.approx(0)
    assert r.center.z == pytest.approx(0)
    # Normal is always (0,0,1) in 2D
    assert r.normal.x == pytest.approx(0)
    assert r.normal.y == pytest.approx(0)
    assert r.normal.z == pytest.approx(1)
    assert r.radius == pytest.approx(2.5)
```

### E7. Sphere

In N2, a "Sphere" represents a circle in the 2D plane.

```python
def test_entity_sphere_opns_round_trip(b):
    """E7: create Sphere(center=(2,-1,0), radius=2.5) → analyze → assert."""
    mv = create_entity(b, Sphere(Point(2, -1, 0), 2.5))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Sphere), f"Got {type(r).__name__}"
    assert not r.is_imaginary
    assert r.center.x == pytest.approx(2)
    assert r.center.y == pytest.approx(-1)
    assert r.center.z == pytest.approx(0)
    assert r.radius == pytest.approx(2.5)
```

### E8. Space

```python
def test_entity_space_opns_round_trip(b):
    """E8: create Space(scale=2.5) → analyze → assert."""
    mv = create_entity(b, Space(scale=2.5))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Space), f"Got {type(r).__name__}"
    assert r.scale == pytest.approx(2.5)
```

---

## 2. Operator Round-Trips (9 tests)

### O1. Rotor

```python
def test_operator_rotor_round_trip(b):
    """O1: create Rotor(π/2, z-axis) → analyze → assert angle & axis.
    
    2D rotation is always about the z-axis.
    """
    mv = create_operator(b, Rotor(math.pi / 2, Direction(0, 0, 1)))
    r = analyze_operator(mv)
    assert isinstance(r, Rotor), f"Got {type(r).__name__}"
    assert r.angle == pytest.approx(math.pi / 2)
    assert r.axis.x == pytest.approx(0)
    assert r.axis.y == pytest.approx(0)
    assert r.axis.z == pytest.approx(1)
```

### O2. Translator

```python
def test_operator_translator_round_trip(b):
    """O2: create Translator(2,-1,0) → analyze → assert vector.
    
    N2 convention: T = 1 − ½·t·e∞
    """
    mv = create_operator(b, Translator(Direction(2, -1, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, Translator), f"Got {type(r).__name__}"
    assert r.vector.x == pytest.approx(2)
    assert r.vector.y == pytest.approx(-1)
    assert r.vector.z == pytest.approx(0)
```

### O3. ReflectionLine

N2 `analyze_operator` returns `ReflectionLine` from two paths:
- Grade‑1 pure Euclidean (line IPNS)
- Grade‑2 d∧e∞ (OPNS line through origin)

`create_operator` creates the grade‑2 form. Both analysis paths are accepted
for now (to be clarified later).

```python
def test_operator_reflection_line_round_trip(b):
    """O3: create ReflectionLine(direction=(1,2,0)) → analyze → assert direction."""
    mv = create_operator(b, ReflectionLine(Direction(1, 2, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionLine), f"Got {type(r).__name__}"
    # Direction is unit-normalized
    unit = Direction(1, 2, 0).norm()
    assert r.direction.x == pytest.approx(unit.x)
    assert r.direction.y == pytest.approx(unit.y)
    assert r.direction.z == pytest.approx(0)
```

### O4. ReflectionOrigin

```python
def test_operator_reflection_origin_round_trip(b):
    """O4: create ReflectionOrigin → analyze → assert type (no fields)."""
    mv = create_operator(b, ReflectionOrigin())
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionOrigin), f"Got {type(r).__name__}"
```

### O5. Inversion

```python
def test_operator_inversion_round_trip(b):
    """O5: create Inversion(center=(2,-1,0), radius=2.5) → analyze → assert."""
    mv = create_operator(b, Inversion(Point(2, -1, 0), 2.5))
    r = analyze_operator(mv)
    assert isinstance(r, Inversion), f"Got {type(r).__name__}"
    assert r.center.x == pytest.approx(2)
    assert r.center.y == pytest.approx(-1)
    assert r.center.z == pytest.approx(0)
    assert r.radius == pytest.approx(2.5)
```

### O6. Dilator (origin)

```python
def test_operator_dilator_origin_round_trip(b):
    """O6: create Dilator(factor=2.0) → analyze → assert factor, origin=(0,0,0)."""
    mv = create_operator(b, Dilator(2.0))
    r = analyze_operator(mv)
    assert isinstance(r, Dilator), f"Got {type(r).__name__}"
    assert r.factor == pytest.approx(2.0)
    assert r.origin.x == pytest.approx(0)
    assert r.origin.y == pytest.approx(0)
    assert r.origin.z == pytest.approx(0)
```

### O7. Dilator (displaced)

General dilator form: `T · D · T̃` (reverse translate, dilate, forward translate).

```python
def test_operator_dilator_displaced_round_trip(b):
    """O7: create Dilator(factor=2.0, origin=(1,0,0)) → analyze → assert factor & origin."""
    mv = create_operator(b, Dilator(2.0, origin=Point(1, 0, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, Dilator), f"Got {type(r).__name__}"
    assert r.factor == pytest.approx(2.0)
    assert r.origin.x == pytest.approx(1)
    assert r.origin.y == pytest.approx(0)
    assert r.origin.z == pytest.approx(0)
```

### O8. Motor

Motor = T · R. Use a translator perpendicular to the rotation plane (z-axis)
to get a clean Motor with a grade‑3 term (the 2D equivalent of grade‑4).

```python
def test_operator_motor_round_trip(b):
    """O8: create Motor(T(1,0,0), R(π/2, z)) → analyze → assert both parts."""
    mv = create_operator(
        b,
        Motor(
            rotor=Rotor(math.pi / 2, Direction(0, 0, 1)),
            translator=Translator(Direction(1, 0, 0)),
        ),
    )
    r = analyze_operator(mv)
    assert isinstance(r, Motor), f"Got {type(r).__name__}"
    assert r.rotor.angle == pytest.approx(math.pi / 2)
    assert r.rotor.axis.z == pytest.approx(1)
    assert r.translator.vector.x == pytest.approx(1)
    assert r.translator.vector.y == pytest.approx(0)
    assert r.translator.vector.z == pytest.approx(0)
```

### O9. GeneralRotor

```python
def test_operator_general_rotor_round_trip(b):
    """O9: create GeneralRotor(π/2, z-axis, origin=(1,0,0)) → analyze."""
    mv = create_operator(b, GeneralRotor(math.pi / 2, Direction(0, 0, 1), Point(1, 0, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, GeneralRotor), f"Got {type(r).__name__}"
    assert r.angle == pytest.approx(math.pi / 2)
    assert r.axis.x == pytest.approx(0)
    assert r.axis.y == pytest.approx(0)
    assert r.axis.z == pytest.approx(1)
    assert r.origin.x == pytest.approx(1)
    assert r.origin.y == pytest.approx(0)
    assert r.origin.z == pytest.approx(0)
```

---

## 3. Operator Application Tests (9 tests)

### A1. Translator: point displacement

```python
def test_apply_translator_point_displacement(b):
    """A1: Translator(3,0,0) applied to origin → Point(3,0,0)."""
    p = create_entity(b, Point(0, 0, 0))
    T = create_operator(b, Translator(Direction(3, 0, 0)))
    result = T.gp(p).gp(T.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(3)
    assert r.y == pytest.approx(0)
    assert r.z == pytest.approx(0)
```

### A2. Rotor: point rotation by 90° about z

```python
def test_apply_rotor_point_rotation_z(b):
    """A2: Rotor(90°, z) on (1,0,0) → Point(0,1,0)."""
    p = create_entity(b, Point(1, 0, 0))
    R = create_operator(b, Rotor(math.pi / 2, Direction(0, 0, 1)))
    result = R.gp(p).gp(R.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(0, abs=1e-6)
    assert r.y == pytest.approx(1, abs=1e-6)
    assert r.z == pytest.approx(0)
```

### A3. ReflectionLine: mirror point across x-axis

```python
def test_apply_reflection_line_point_mirror_x(b):
    """A3: ReflectionLine(x-axis) on (3,1,0) → Point(3,-1,0)."""
    p = create_entity(b, Point(3, 1, 0))
    L = create_operator(b, ReflectionLine(Direction(1, 0, 0)))
    result = L.gp(p).gp(L.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(3)
    assert r.y == pytest.approx(-1)
    assert r.z == pytest.approx(0)
```

### A4. ReflectionOrigin: point reflection

```python
def test_apply_reflection_origin_point_negation(b):
    """A4: ReflectionOrigin on (5,-3,0) → Point(-5,3,0)."""
    p = create_entity(b, Point(5, -3, 0))
    O = create_operator(b, ReflectionOrigin())
    result = O.gp(p).gp(O.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(-5)
    assert r.y == pytest.approx(3)
    assert r.z == pytest.approx(0)
```

### A5. Inversion: spherical inversion

```python
def test_apply_inversion_point_inversion(b):
    """A5: Inversion at origin r=1 on (2,0,0) → Point(0.5,0,0).
    
    Spherical inversion: p → p·r²/|p|².
    """
    p = create_entity(b, Point(2, 0, 0))
    S = create_operator(b, Inversion(Point(0, 0, 0), 1.0))
    result = S.gp(p).gp(S.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(0.5)
    assert r.y == pytest.approx(0)
    assert r.z == pytest.approx(0)
```

### A6. Dilator (origin): scale about origin

```python
def test_apply_dilator_origin_point_scaling(b):
    """A6: Dilator(2.0) on (3,0,0) → Point(6,0,0).
    
    Dilator scales about the origin by factor d.
    """
    p = create_entity(b, Point(3, 0, 0))
    D = create_operator(b, Dilator(2.0))
    result = D.gp(p).gp(D.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(6)
    assert r.y == pytest.approx(0)
    assert r.z == pytest.approx(0)
```

### A7. Dilator (displaced): scale about non-origin center

```python
def test_apply_dilator_displaced_point_scaling(b):
    """A7: Dilator(2.0, origin=(1,0,0)) on (2,0,0) → Point(3,0,0).
    
    General dilator: T·D·T̃.  Relative to center (1,0,0):
    (2,0,0) − (1,0,0) = (1,0,0) → scale by 2 → (2,0,0) + center = (3,0,0).
    """
    p = create_entity(b, Point(2, 0, 0))
    D = create_operator(b, Dilator(2.0, origin=Point(1, 0, 0)))
    result = D.gp(p).gp(D.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(3)
    assert r.y == pytest.approx(0)
    assert r.z == pytest.approx(0)
```

### A8. Motor: rigid motion (translate then rotate)

Motor = T · R. Origin → translate (+1,0,0) → (1,0,0) → rotate 90° about z → (0,1,0).

```python
def test_apply_motor_point_rigid_motion(b):
    """A8: Motor(T(1,0,0), R(90°, z)) on origin → Point(0,1,0)."""
    p = create_entity(b, Point(0, 0, 0))
    M = create_operator(
        b,
        Motor(
            rotor=Rotor(math.pi / 2, Direction(0, 0, 1)),
            translator=Translator(Direction(1, 0, 0)),
        ),
    )
    result = M.gp(p).gp(M.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(0, abs=1e-6)
    assert r.y == pytest.approx(1, abs=1e-6)
    assert r.z == pytest.approx(0)
```

### A9. GeneralRotor: rotation about displaced axis

GeneralRotor(π/2, z-axis, origin=(1,0,0)) rotates about z-axis through x=1.
Point (2,0,0): subtract center → (1,0,0), rotate 90° about z → (0,1,0), add center → (1,1,0).

```python
def test_apply_general_rotor_point_displaced_rotation(b):
    """A9: GeneralRotor(90°, z, at x=1) on (2,0,0) → Point(1,1,0)."""
    p = create_entity(b, Point(2, 0, 0))
    G = create_operator(b, GeneralRotor(math.pi / 2, Direction(0, 0, 1), Point(1, 0, 0)))
    result = G.gp(p).gp(G.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(1, abs=1e-6)
    assert r.y == pytest.approx(1, abs=1e-6)
    assert r.z == pytest.approx(0)
```

---

## 4. Known Limitations

- **N2 ReflectionLine** analyzed from two paths (grade‑1 pure Euclidean + grade‑2 d∧e∞). Both accepted as valid for now — to be clarified later.
- **VersorFactors** fallback for unhandled factor counts. Not testable as round‑trip.
- **No ReflectionPlane** in N2 (lines serve that role in 2D).
- **Imaginary variants** (ImagPointPair, ImagCircle, ImagSphere) deferred.

---

## 5. Differences from N3

| Aspect | N3 | N2 |
|--------|----|----|
| Dimensionality | 3D conformal | 2D conformal |
| Plane entity | Planes in 3D | N/A (plane = line in 2D) |
| ReflectionPlane | Analyzed | N/A (ReflectionLine covers it) |
| Circle | 3D circle (arbitrary normal) | Circle in XY plane (normal always (0,0,1)) |
| Sphere | 3D sphere | Circle in 2D plane |
| Rotor axis | Any direction | Always z-axis (0,0,1) |
| Motor grade‑4 term | Exists | Grade‑3 equivalent |
| Z coordinate | Meaningful | Always 0 |

## 6. Test Count Summary

| Section | Tests |
|---------|-------|
| Entity round-trips | 8 (Point, Direction, PointPair, HPoint, Line, Circle, Sphere, Space) |
| Operator round-trips | 9 (Rotor, Translator, ReflectionLine, ReflectionOrigin, Inversion, Dilator×2, Motor, GeneralRotor) |
| Application tests | 9 (Translator, Rotor, ReflectionLine, ReflectionOrigin, Inversion, Dilator×2, Motor, GeneralRotor) |
| **Total** | **26** |