# Test Plan: N3 Entity & Operator Analysis

**Status:** draft  
**Algebra:** `Algebra.from_name("N3")`  
**Implementation file:** `py/tests/geometry/test_geometry_n3_analysis.py`  
**Prerequisite:** Merge `Dilator` + `GeneralDilator` into single `Dilator(factor, origin=Point(0,0,0))` (T·D·T̃ form for general dilator)

Tests for the N3 conformal `create` ↔ `analyze` round-trip and operator application,
following the golden rules:

1. No `abs()` on signed values
2. No `isinstance` unions in expected type
3. Assert all relevant fields
4. Application test is the ultimate validator
5. Tests must fail when the implementation is wrong

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
    return Algebra.from_name("N3")
```

---

## 1. Entity Round-Trips (9 tests)

### E1. Point

```python
def test_entity_point_opns_round_trip(b):
    """E1: create Point(3,-2,7) → analyze → assert exact."""
    mv = create_entity(b, Point(3, -2, 7))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(3)
    assert r.y == pytest.approx(-2)
    assert r.z == pytest.approx(7)
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
The round-trip must verify the pair reproduces — compare midpoint, separation,
and direction rather than exact point_a/point_b ordering.

```python
def test_entity_point_pair_opns_round_trip(b):
    """E3: create PointPair → analyze → assert midpoint, separation, direction."""
    a = Point(1, 0, 1)
    b_p = Point(3, 0, 2)
    mv = create_entity(b, PointPair(a, b_p))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, PointPair), f"Got {type(r).__name__}"
    assert not r.is_imaginary
    # Verify midpoint
    mid = Point((a.x + b_p.x) / 2, (a.y + b_p.y) / 2, (a.z + b_p.z) / 2)
    r_mid = Point(
        (r.point_a.x + r.point_b.x) / 2,
        (r.point_a.y + r.point_b.y) / 2,
        (r.point_a.z + r.point_b.z) / 2,
    )
    assert r_mid.x == pytest.approx(mid.x)
    assert r_mid.y == pytest.approx(mid.y)
    assert r_mid.z == pytest.approx(mid.z)
    # Verify separation
    sep = math.sqrt((b_p.x - a.x)**2 + (b_p.y - a.y)**2 + (b_p.z - a.z)**2)
    r_sep = math.sqrt(
        (r.point_b.x - r.point_a.x)**2
        + (r.point_b.y - r.point_a.y)**2
        + (r.point_b.z - r.point_a.z)**2
    )
    assert r_sep == pytest.approx(sep)
    # Verify point_a is along −dir, point_b along +dir
    # (direction from point_a to point_b matches (b − a) direction)
    d = Direction(b_p.x - a.x, b_p.y - a.y, b_p.z - a.z)
    r_d = Direction(
        r.point_b.x - r.point_a.x,
        r.point_b.y - r.point_a.y,
        r.point_b.z - r.point_a.z,
    )
    assert r_d.x == pytest.approx(d.x)
    assert r_d.y == pytest.approx(d.y)
    assert r_d.z == pytest.approx(d.z)
```

### E4. HPoint

HPoint is `Cop(p)∧e∞` — a grade‑2 OPNS blade containing e∞ as a factor.
The analysis extracts the point via `_factor_to_point` and weight via `mv·E`.

```python
def test_entity_hpoint_opns_round_trip(b):
    """E4: create HPoint(Point(2,-1,3), weight=2.5) → analyze → assert."""
    mv = create_entity(b, HPoint(Point(2, -1, 3), weight=2.5))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, HPoint), f"Got {type(r).__name__}"
    assert r.point.x == pytest.approx(2)
    assert r.point.y == pytest.approx(-1)
    assert r.point.z == pytest.approx(3)
    assert r.weight == pytest.approx(2.5)
```

### E5. Line

The analysis returns the closest point to the origin on the line and
normalizes the direction to unit length.

```python
def test_entity_line_opns_round_trip(b):
    """E5: create Line(origin=(1,2,3), dir=(1,2,0)) → analyze → assert."""
    direction = Direction(1, 2, 0)
    unit = direction.norm()
    pt = Point(1, 2, 3)
    mv = create_entity(b, Line(pt, direction))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Line), f"Got {type(r).__name__}"
    # Direction normalized and preserves sign
    assert r.direction.x == pytest.approx(unit.x)
    assert r.direction.y == pytest.approx(unit.y)
    assert r.direction.z == pytest.approx(unit.z)
    # Analyzed origin must lie on the line: (r.origin − pt) ∥ direction
    dx = r.origin.x - pt.x
    dy = r.origin.y - pt.y
    dz = r.origin.z - pt.z
    cross_x = direction.y * dz - direction.z * dy
    cross_y = direction.z * dx - direction.x * dz
    cross_z = direction.x * dy - direction.y * dx
    assert cross_x == pytest.approx(0, abs=1e-6)
    assert cross_y == pytest.approx(0, abs=1e-6)
    assert cross_z == pytest.approx(0, abs=1e-6)
```

### E6. Circle

```python
def test_entity_circle_opns_round_trip(b):
    """E6: create Circle(center=(1,0,2), normal=(0,1,0), radius=2.5) → analyze."""
    normal = Direction(0, 1, 0)
    unit = normal.norm()
    mv = create_entity(b, Circle(Point(1, 0, 2), normal, 2.5))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Circle), f"Got {type(r).__name__}"
    assert not r.is_imaginary
    assert r.center.x == pytest.approx(1)
    assert r.center.y == pytest.approx(0)
    assert r.center.z == pytest.approx(2)
    assert r.normal.x == pytest.approx(unit.x)
    assert r.normal.y == pytest.approx(unit.y)
    assert r.normal.z == pytest.approx(unit.z)
    assert r.radius == pytest.approx(2.5)
```

### E7. Plane

```python
def test_entity_plane_opns_round_trip(b):
    """E7: create Plane(point=(3,-2,1), normal=(1,3,0)) → analyze → assert."""
    normal = Direction(1, 3, 0)
    unit = normal.norm()
    pt = Point(3, -2, 1)
    mv = create_entity(b, Plane(pt, normal))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Plane), f"Got {type(r).__name__}"
    # Normal must match the unit-length direction
    assert r.normal.x == pytest.approx(unit.x)
    assert r.normal.y == pytest.approx(unit.y)
    assert r.normal.z == pytest.approx(unit.z)
    # Analyzed point must lie on the plane: n·p = d
    d = normal.x * pt.x + normal.y * pt.y + normal.z * pt.z
    d_scaled = d / normal.mag()
    d_analyzed = (
        r.normal.x * r.point.x + r.normal.y * r.point.y + r.normal.z * r.point.z
    )
    assert d_analyzed == pytest.approx(d_scaled)
```

### E8. Sphere

```python
def test_entity_sphere_opns_round_trip(b):
    """E8: create Sphere(center=(2,-1,3), radius=2.5) → analyze → assert."""
    mv = create_entity(b, Sphere(Point(2, -1, 3), 2.5))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Sphere), f"Got {type(r).__name__}"
    assert not r.is_imaginary
    assert r.center.x == pytest.approx(2)
    assert r.center.y == pytest.approx(-1)
    assert r.center.z == pytest.approx(3)
    assert r.radius == pytest.approx(2.5)
```

### E9. Space

```python
def test_entity_space_opns_round_trip(b):
    """E9: create Space(scale=2.5) → analyze → assert."""
    mv = create_entity(b, Space(scale=2.5))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Space), f"Got {type(r).__name__}"
    assert r.scale == pytest.approx(2.5)
```

---

## 2. Operator Round-Trips (10 tests)

### O1. Rotor

```python
def test_operator_rotor_round_trip(b):
    """O1: create Rotor(π/2, z-axis) → analyze → assert angle & axis."""
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
    """O2: create Translator(2,-1,3) → analyze → assert vector.
    
    N3 convention: T = 1 − ½·t·e∞
    Analysis: tᵢ = +2 · mv·(eᵢ∧e₀) / mv[0]
    """
    mv = create_operator(b, Translator(Direction(2, -1, 3)))
    r = analyze_operator(mv)
    assert isinstance(r, Translator), f"Got {type(r).__name__}"
    assert r.vector.x == pytest.approx(2)
    assert r.vector.y == pytest.approx(-1)
    assert r.vector.z == pytest.approx(3)
```

### O3. ReflectionLine

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
    assert r.direction.z == pytest.approx(unit.z)
```

### O4. ReflectionPlane

```python
def test_operator_reflection_plane_round_trip(b):
    """O4: create ReflectionPlane(normal=(0,0,1)) → analyze → assert normal."""
    mv = create_operator(b, ReflectionPlane(Direction(0, 0, 1)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionPlane), f"Got {type(r).__name__}"
    assert r.normal.x == pytest.approx(0)
    assert r.normal.y == pytest.approx(0)
    assert r.normal.z == pytest.approx(1)
```

### O5. ReflectionOrigin

```python
def test_operator_reflection_origin_round_trip(b):
    """O5: create ReflectionOrigin → analyze → assert type (no fields)."""
    mv = create_operator(b, ReflectionOrigin())
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionOrigin), f"Got {type(r).__name__}"
```

### O6. Inversion

```python
def test_operator_inversion_round_trip(b):
    """O6: create Inversion(center=(2,-1,3), radius=2.5) → analyze → assert."""
    mv = create_operator(b, Inversion(Point(2, -1, 3), 2.5))
    r = analyze_operator(mv)
    assert isinstance(r, Inversion), f"Got {type(r).__name__}"
    assert r.center.x == pytest.approx(2)
    assert r.center.y == pytest.approx(-1)
    assert r.center.z == pytest.approx(3)
    assert r.radius == pytest.approx(2.5)
```

### O7. Dilator (origin)

```python
def test_operator_dilator_origin_round_trip(b):
    """O7: create Dilator(factor=2.0) → analyze → assert factor, origin=(0,0,0)."""
    mv = create_operator(b, Dilator(2.0))
    r = analyze_operator(mv)
    assert isinstance(r, Dilator), f"Got {type(r).__name__}"
    assert r.factor == pytest.approx(2.0)
    assert r.origin.x == pytest.approx(0)
    assert r.origin.y == pytest.approx(0)
    assert r.origin.z == pytest.approx(0)
```

### O8. Dilator (displaced)

General dilator form: `T · D · T̃` (reverse translate, dilate, forward translate).
Analysis extracts `d_part = dil | E` and `t_part` via algebraic identities
(no blade factorization needed — see `dev/src/entities_04.py`).

```python
def test_operator_dilator_displaced_round_trip(b):
    """O8: create Dilator(factor=2.0, origin=(1,0,0)) → analyze → assert factor & origin."""
    mv = create_operator(b, Dilator(2.0, origin=Point(1, 0, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, Dilator), f"Got {type(r).__name__}"
    assert r.factor == pytest.approx(2.0)
    assert r.origin.x == pytest.approx(1)
    assert r.origin.y == pytest.approx(0)
    assert r.origin.z == pytest.approx(0)
```

### O9. Motor

Motor = T · R. Use a translator perpendicular to the rotation plane to get
a clean Motor with a grade‑4 term (required for Motor classification).

```python
def test_operator_motor_round_trip(b):
    """O9: create Motor(T(0,0,1), R(π/2, z)) → analyze → assert both parts."""
    mv = create_operator(
        b,
        Motor(
            rotor=Rotor(math.pi / 2, Direction(0, 0, 1)),
            translator=Translator(Direction(0, 0, 1)),
        ),
    )
    r = analyze_operator(mv)
    assert isinstance(r, Motor), f"Got {type(r).__name__}"
    assert r.rotor.angle == pytest.approx(math.pi / 2)
    assert r.rotor.axis.z == pytest.approx(1)
    assert r.translator.vector.x == pytest.approx(0)
    assert r.translator.vector.y == pytest.approx(0)
    assert r.translator.vector.z == pytest.approx(1)
```

### O10. GeneralRotor

```python
def test_operator_general_rotor_round_trip(b):
    """O10: create GeneralRotor(π/2, z-axis, origin=(1,0,0)) → analyze."""
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

## 3. Operator Application Tests (10 tests)

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

### A4. ReflectionPlane: reflection across plane z=0

```python
def test_apply_reflection_plane_point_mirror(b):
    """A4: ReflectionPlane(normal=z) on (1,2,5) → Point(1,2,-5)."""
    p = create_entity(b, Point(1, 2, 5))
    F = create_operator(b, ReflectionPlane(Direction(0, 0, 1)))
    result = F.gp(p).gp(F.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(-5)
```

### A5. ReflectionOrigin: point reflection

```python
def test_apply_reflection_origin_point_negation(b):
    """A5: ReflectionOrigin on (5,-3,2) → Point(-5,3,-2)."""
    p = create_entity(b, Point(5, -3, 2))
    O = create_operator(b, ReflectionOrigin())
    result = O.gp(p).gp(O.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(-5)
    assert r.y == pytest.approx(3)
    assert r.z == pytest.approx(-2)
```

### A6. Inversion: point on unit sphere is fixed

```python
def test_apply_inversion_point_on_sphere(b):
    """A6: Inversion at origin r=1 on (2,0,0) → Point(0.5,0,0).
    
    Spherical inversion: p → p·r²/|p|².
    Point (2,0,0) with r=1 → (2·1/4, 0, 0) = (0.5, 0, 0).
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

### A7. Dilator (origin): scale about origin

```python
def test_apply_dilator_origin_point_scaling(b):
    """A7: Dilator(2.0) on (3,0,0) → Point(6,0,0).
    
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

### A8. Dilator (displaced): scale about non-origin center

```python
def test_apply_dilator_displaced_point_scaling(b):
    """A8: Dilator(2.0, origin=(1,0,0)) on (2,0,0) → Point(3,0,0).
    
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

### A9. Motor: rigid motion (translate then rotate)

Motor = T · R. Origin → translate (+1,0,0) → (1,0,0) → rotate 90° about z → (0,1,0).

```python
def test_apply_motor_point_rigid_motion(b):
    """A9: Motor(T(1,0,0), R(90°, z)) on origin → Point(0,1,0)."""
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

### A10. GeneralRotor: rotation about displaced axis

GeneralRotor(π/2, z-axis, origin=(1,0,0)) rotates about z-axis through x=1.
Point (2,0,0): subtract center → (1,0,0), rotate 90° about z → (0,1,0), add center → (1,1,0).

```python
def test_apply_general_rotor_point_displaced_rotation(b):
    """A10: GeneralRotor(90°, z, at x=1) on (2,0,0) → Point(1,1,0)."""
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

- **VersorFactors** fallback for unhandled factor counts (e.g. 3‑factor mixed dilator+rotor). Not testable as round‑trip — this is a genuine fallback, not a bug.
- **TripleReflection** not returned by N3 `analyze_operator` (only in PGA3). Not tested.
- **Imaginary variants** (ImagPointPair, ImagCircle, ImagSphere) deferred — require specialized create functions (`create_imag_point_pair`, `create_imag_circle`). The `create` dispatcher handles them transparently via `is_imaginary=True`.

---

## 5. Test Count Summary

| Section | Tests |
|---------|-------|
| Entity round-trips | 9 (Point, Direction, PointPair, HPoint, Line, Circle, Plane, Sphere, Space) |
| Operator round-trips | 10 (Rotor, Translator, ReflectionLine, ReflectionPlane, ReflectionOrigin, Inversion, Dilator×2, Motor, GeneralRotor) |
| Application tests | 10 (Translator, Rotor, ReflectionLine, ReflectionPlane, ReflectionOrigin, Inversion, Dilator×2, Motor, GeneralRotor) |
| **Total** | **29** |