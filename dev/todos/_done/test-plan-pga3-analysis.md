# Test Plan: PGA3 Entity & Operator Analysis

**Status:** draft — aligned with `test-guide-algebra-round-trip.md` (2026-08-07)
**Algebra:** `BasisPGA3()` via `Algebra.from_name("PGA3")`
**Implementation file:** `py/tests/geometry/test_geometry_pga3_analysis.py`

Tests for the PGA3 `create` ↔ `analyze` round-trip and operator application,
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

@pytest.fixture(scope="module")
def b():
    return Algebra.from_name("PGA3")
```

---

## 1. Entity Round-Trips

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

### E3. Plane

The analysis returns the closest point to the origin on the plane and
normalizes the normal to unit length.  The normal must round-trip with the
same sign.  The point is verified by checking it lies on the plane (n·p = d).

Use a non-trivial normal so all components are constrained:

```python
def test_entity_plane_opns_round_trip(b):
    """E3: create Plane(point=(3,-2,1), normal=(1,3,0)) → analyze → assert."""
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

### E4. Line

The analysis returns the closest point to the origin on the line, not
necessarily the construction point.  The direction is normalized to unit
length but must preserve the same sign.  The origin is verified by checking
it lies on the line: (r.origin − pt) ∥ direction.

```python
def test_entity_line_opns_round_trip(b):
    """E4: create Line(origin=(1,2,3), dir=(1,2,0)) → analyze → assert."""
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

### E5. Space

```python
def test_entity_space_opns_round_trip(b):
    """E5: create Space(scale=2.5) → analyze → assert."""
    mv = create_entity(b, Space(scale=2.5))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Space), f"Got {type(r).__name__}"
    assert r.scale == pytest.approx(2.5)
```

---

## 2. Operator Round-Trips

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
    
    Creation: T = 1 + 0.5·(dx·e₁∧e₀ + …)  (plus sign)
    Analysis: dx = +2.0 * mv[9]              (plus sign — must match!)
    """
    mv = create_operator(b, Translator(Direction(2, -1, 3)))
    r = analyze_operator(mv)
    assert isinstance(r, Translator), f"Got {type(r).__name__}"
    assert r.vector.x == pytest.approx(2)
    assert r.vector.y == pytest.approx(-1)
    assert r.vector.z == pytest.approx(3)
```

### O3. Motor

```python
def test_operator_motor_round_trip(b):
    """O3: create Motor(T(1,0,0), R(π/2, z)) → analyze → assert both parts."""
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
```

### O4. ReflectionPlane

```python
def test_operator_reflection_plane_round_trip(b):
    """O4: create ReflectionPlane(normal=(0,0,1)) → analyze → assert normal."""
    mv = create_operator(b, ReflectionPlane(Direction(0, 0, 1)))
    r = analyze_operator(mv)
    # Reflection is an alias for ReflectionPlane in operators.py
    assert isinstance(r, ReflectionPlane | Reflection), f"Got {type(r).__name__}"
    assert r.normal.x == pytest.approx(0)
    assert r.normal.y == pytest.approx(0)
    assert r.normal.z == pytest.approx(1)
```

Note: `analysis_pga3.analyze_operator` returns `Reflection` which is the
backward-compatibility alias for `ReflectionPlane`. The `isinstance` check
accepts either.

### O5. GeneralRotor

```python
def test_operator_general_rotor_round_trip(b):
    """O5: create GeneralRotor(π/2, z-axis, origin=(1,0,0)) → analyze.
    
    GeneralRotor now uses flat fields (angle, axis, origin) — not
    the old nested (Rotor, Translator) constructor.
    """
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

### O6. TripleReflection

No `create_operator` function exists for `TripleReflection`; the versor must be
built manually as the product of three grade-1 plane vectors.

```python
def test_operator_triple_reflection_round_trip(b):
    """O6: manual triple reflection → analyze → assert three planes."""
    # Build three orthogonal planes through the origin
    e1 = b.multivector({E1: 1.0})
    e2 = b.multivector({E2: 1.0})
    e3 = b.multivector({E3: 1.0})
    mv = e1.op(e2).op(e3)  # grade-3 trivector (but as versor product, grades 1+3)
    
    # Actually we need the geometric product, not outer product:
    mv = e1.gp(e2).gp(e3)
    
    r = analyze_operator(mv)
    assert isinstance(r, TripleReflection), f"Got {type(r).__name__}"
    assert len(r.planes) == 3
```

**Edge case**: factorization of 3 grade-1 vectors may produce different plane
orderings. Accept the set of planes, not a specific ordering.

---

## 3. Operator Application Tests

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

### A3. Motor: rigid motion (translate + rotate)

Motor = T · R: translate first, then rotate.

Origin → translate (+1,0,0) → (1,0,0) → rotate 90° about z → (0,1,0).

```python
def test_apply_motor_point_rigid_motion(b):
    """A3: Motor(T(1,0,0), R(90°, z)) on origin → Point(0,1,0)."""
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

### A4. ReflectionPlane: reflection across plane z=0

Reflection in the plane z=0 flips the z-component.

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

### A5. GeneralRotor: rotation about displaced axis

GeneralRotor(π/2, z-axis, origin=(1,0,0)) rotates about z-axis through x=1.
Point (2,0,0): subtract center → (1,0,0), rotate 90° about z → (0,1,0), add
center → (1,1,0).

```python
def test_apply_general_rotor_point_displaced_rotation(b):
    """A5: GeneralRotor(90°, z, at x=1) on (2,0,0) → Point(1,1,0)."""
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

### ReflectionLine and ReflectionOrigin (NOT TESTED)

`create_pga3.py` has creation functions for `ReflectionLine` and
`ReflectionOrigin`, but `analysis_pga3.analyze_operator` does **not** return
these types. It only returns: `Reflection | Rotor | Translator | Motor |
GeneralRotor | TripleReflection`.

This means **round-trip and application tests cannot be written** for
`ReflectionLine` and `ReflectionOrigin` until the analysis is extended.

If these are added later, follow the standard patterns from sections 2–3 above.

### TripleReflection creation

No `create_operator` dispatches to a `TripleReflection` creator. The test
must build the versor manually from three grade-1 vectors (planes). This is
acceptable as a limitation note — the test documents the constraint upfront.

---

## 5. Test Count Summary

| Section | Tests | Status |
|---------|-------|--------|
| Entity round-trips | 5 (Point, Direction, Plane, Line, Space) | planned |
| Operator round-trips | 6 (Rotor, Translator, Motor, ReflectionPlane, GeneralRotor, TripleReflection) | planned |
| Application tests | 5 (Translator, Rotor, Motor, ReflectionPlane, GeneralRotor) | planned |
| **Total** | **16** | |

Not included (analysis limitation): ReflectionLine, ReflectionOrigin.