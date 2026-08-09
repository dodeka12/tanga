# Algebra Round-Trip Test Guide

**Status:** final  
**Created:** 2026-08-07

## Purpose

This document defines the pattern for writing entity and operator round-trip
tests for any geometric algebra (PGA2, PGA3, N2, N3, E2, E3, P2, P3).

A **round-trip test** validates that `analyze(create(obj))` reproduces the
original geometric object exactly — same type, same coordinates, same sign.

## Golden Rules

1. **No `abs()` on signed values.** A point at `(3, -2)` must round-trip as
   `(3, -2)`, never `(-3, 2)`.  `abs()` hides sign flips caused by blade
   factorization ordering.  If you need `abs()`, the analysis function is
   broken.

2. **No `isinstance` unions in the expected type assertion.** A test for a
   `ReflectionOrigin` must assert `isinstance(r, ReflectionOrigin)`, not
   `isinstance(r, (ReflectionOrigin, Rotor, GeneralRotor))`.  The latter makes
   the test pass for three different types — it's useless.

3. **Assert all relevant fields, not just type.** For an operator, check angle,
   axis components, translation vector, origin point, direction — whatever the
   operator carries.  For an entity, check all coordinates.

4. **The application test is the ultimate validator.** Even if the round-trip
   analysis passes, apply the operator to a known entity and verify the
   geometric result.  A `Translator(3,0)` applied to the origin must produce
   `Point(3, 0)`, not `Point(-3, 0)`.  A `Rotor(90°, z)` applied to `(1,0)`
   must produce `(0, 1)`.

5. **Tests must fail when the implementation is wrong.** If a test passes
   despite a known bug, the test is broken.  Skip tests only for genuine
   limitations (e.g. "this algebra can't construct a 3-factor versor"), not
   for bugs you plan to fix later.

## Test Structure

Every algebra test file should have three sections:

### 1. Entity Round-Trips

Test every entity type supported by the algebra.  Pattern:

```python
def test_entity_<name>_opns_round_trip(b):
    """E#: create <Entity> → analyze → assert exact fields."""
    mv = create_entity(b, <Entity>(<params>))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, <Entity>)
    assert r.<field1> == pytest.approx(<expected1>)
    assert r.<field2> == pytest.approx(<expected2>)
    ...
```

**Entity types per algebra (typical):**

| Algebra | Entities |
|---------|----------|
| PGA2    | Point, Direction, Line, Space |
| PGA3    | Point, Direction, Line, Plane, Space |
| N2      | Point, Direction, PointPair, HPoint, Line, Circle, Sphere, Space |
| N3      | Point, Direction, PointPair, HPoint, Line, Circle, Plane, Sphere, Space |
| E2, P2  | Point, Direction |
| E3, P3  | Point, Direction, Line, Plane |

**Important:** Every entity that can be created must also be analyzable.
If `create(Direction(...))` succeeds but `analyze(..., opns=True)` raises,
fix the analysis — don't test for the exception.

**Picking test coordinates:**
- Use distinct signed values: `Point(3, -2, 0)` is better than `Point(1, 1, 0)`
  because sign flips in either coordinate are immediately visible.
- Avoid points at the origin `(0,0,0)` — they're invariant under many
  transformations and hide bugs.
- Use non-unit radii for spheres/circles: `Sphere(center=..., radius=2.5)`.

### 2. Operator Round-Trips

Test every operator type supported by the algebra.  Pattern:

```python
def test_operator_<name>_round_trip(b):
    """O#: create <Operator> → analyze → assert exact fields."""
    mv = create_operator(b, <Operator>(<params>))
    r = analyze_operator(mv)
    assert isinstance(r, <Operator>)
    assert r.<field1> == pytest.approx(<expected1>)
    assert r.<field2> == pytest.approx(<expected2>)
    ...
```

**Operator types per algebra (typical):**

| Algebra | Operators |
|---------|-----------|
| PGA2    | Rotor, Translator, Motor, GeneralRotor, ReflectionLine, ReflectionOrigin |
| PGA3    | Rotor, Translator, Motor, GeneralRotor, Reflection, ReflectionLine, ReflectionOrigin |
| N2      | Rotor, Translator, Motor, GeneralRotor, ReflectionLine, ReflectionOrigin, Inversion, Dilator, GeneralDilator |
| N3      | Rotor, Translator, Motor, GeneralRotor, ReflectionLine, ReflectionPlane, ReflectionOrigin, Inversion, Dilator, GeneralDilator |
| E2, P2  | Rotor, (ReflectionLine) |
| E3, P3  | Rotor, ReflectionPlane |

**Operator-specific assertions:**
- **Rotor**: angle, all axis components
- **Translator**: vector x, y, z
- **Motor**: rotor.angle, rotor.axis, translator.vector
- **GeneralRotor**: angle, axis, origin
- **ReflectionLine/ReflectionPlane**: direction/normal components
- **Inversion**: center, radius
- **Dilator**: factor
- **GeneralDilator**: factor, translator.vector

**Edge case:** Some operators may factorize differently in different algebras
(e.g. PGA2 Motor may factor to 2 or 4 grade-1 vectors depending on the
translator product).  If the type can vary, document the reason in the test
and accept the union, but still assert the geometric content fields.

### 3. Operator Application Tests

Verify that operators actually do what they claim.  This catches bugs that
round-trip analysis misses (e.g. wrong sign in the MV construction that the
analysis compensates for).

**Pattern:**

```python
def test_apply_<operator>_<entity>_<scenario>(b):
    """A#: <description>.  Create operator, create entity, apply via sandwich,
    analyze result, assert expected geometric transformation."""
    p = create_entity(b, <Entity>(<start position>))
    V = create_operator(b, <Operator>(<params>))
    result = V * p * V.rev()
    r = analyze_entity(result, opns=True)
    assert isinstance(r, <Entity>)
    assert r.<field> == pytest.approx(<expected>, abs=1e-6)
```

**Scaffolded sandwich application:**
- `V * p * V.rev()` — the versor sandwich

**Verification:** The expected result must be derived from **first principles**:
- **Translator(t)** → `p + t`
- **Rotor(90°, z)** on `(1,0)` → `(0, 1)`
- **ReflectionOrigin** on `(x,y)` → `(-x, -y)`
- **ReflectionLine(d)** on `p` → `p` flipped across the line through origin
- **Motor(T,R)** on origin → `T·R·0·R̃·T̃` = translate origin, then rotate (or vice versa depending on convention)
- **GeneralRotor(R, center c)** on `p` → rotate `(p-c)` by `R`, add `c` back

**Document the derivation** in a comment above the assertions.

## Pitfalls & Fixes

### Pitfall 1: `abs()` hiding sign flips

```python
# BROKEN — passes for (3,-2), (-3,2), (3,2), (-3,-2)
assert abs(r.x) == pytest.approx(3)
assert abs(r.y) == pytest.approx(2)

# FIXED — only passes for (3,-2)
assert r.x == pytest.approx(3)
assert r.y == pytest.approx(-2)
```

### Pitfall 2: Weak type assertions

```python
# BROKEN — passes for ReflectionOrigin, Rotor, or GeneralRotor
assert isinstance(r, (ReflectionOrigin, Rotor, GeneralRotor))

# FIXED
assert isinstance(r, ReflectionOrigin), f"Got {type(r).__name__}"
```

### Pitfall 3: Testing for exceptions instead of fixing the analysis

```python
# BROKEN — tests the bug instead of fixing it
with pytest.raises(ValueError):
    mv = create_entity(b, Direction(1, 0, 0))
    analyze_entity(mv, opns=True)

# FIXED — Direction round-trip works
def test_entity_direction_opns_round_trip(b):
    mv = create_entity(b, Direction(1, 2, 0))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Direction)
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
```

### Pitfall 4: `skip` for bugs

```python
# BROKEN — hides a real bug
@pytest.mark.skip(reason="BUG: gives (1,4) not (1,2)")
def test_apply_general_rotor(b):
    pass

# FIXED — after fixing the bug, the test actually asserts
def test_apply_general_rotor_point_displaced_rotation(b):
    ...
    assert r.x == pytest.approx(1, abs=1e-6)
    assert r.y == pytest.approx(2, abs=1e-6)
```

### Pitfall 5: Analysis sign inconsistencies with creation

If `create(T = 1 + 0.5·t·e₀)` then `_translator_from_versor` must use
`dx = +2.0 * mv[5]`, **not** `dx = -2.0 * mv[5]`.  The analysis must match
the creation formula exactly.  Any sign difference between creation and
analysis will cause the round-trip test to fail — which is exactly what the
test is supposed to catch.

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
    return Algebra.from_name("<ALGEBRA>")
```

## Implementation Checklist for a New Algebra

1. [ ] List all entity types supported by the algebra.
2. [ ] Write one round-trip test per entity type with exact field assertions.
3. [ ] List all operator types supported by the algebra.
4. [ ] Write one round-trip test per operator type with exact field assertions.
5. [ ] Write one application test per operator type (sandwich + analyze result).
6. [ ] Run the suite.  Every failure is a real bug — fix the code, not the test.
7. [ ] If a test must be skipped, document the **limitation** (not a bug):
   `@pytest.mark.skip(reason="Limitation: ...")`