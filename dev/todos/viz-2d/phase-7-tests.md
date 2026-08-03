# Phase 7 — Tests

Unit tests for 2D algebra round‑trips and integration tests for the 2D
visualization mode.

## Test Directory Structure

All tests go under `py/tests/`. Use `pytest` as the test framework.

## Test Files to Create

### `py/tests/test_basis_2d.py` — Basis Class Smoke Tests

Verify each 2D basis class initializes correctly and basic operations work.

```python
# Tests:
# - Algebra.from_name("E2") returns BasisE2 instance
# - Algebra.from_name("P2") returns BasisP2 instance
# - Algebra.from_name("N2") returns BasisN2 instance
# - Algebra.from_name("PGA2") returns BasisPGA2 instance
# - E2: e1 * e2 == e12
# - P2: point(3, 4) has e3=1 component
# - N2: einf² = 0 (null), eo² = 0 (null), einf·eo = -1
# - PGA2: e0² = 0 (null)
# - Each basis: pseudoscalar_id is correct
# - Each basis: algebra_dim matches 2^dim
# - PGA2 is recognized before N2 in isinstance checks
```

### `py/tests/test_geometry_e2.py` — E2 Round‑Trip Tests

```python
# Entity round‑trips:
# - Direction: create_direction(3, 4, 0) → MV → analyze_entity(mv) → Direction(3, 4, 0)
# - Line through origin: create_line(Point(0,0,0), Dir(1,0,0)) → MV → analyze_entity(mv)
#   (may return Direction, since E2 can't distinguish)
# - Plane through origin: create_plane(Plane(Point(0,0,0), Dir(0,1,0)))
#   → MV → analyze_entity(mv, opns=True) → Plane
# - Space: create_space(scale=2) → MV → analyze_entity(mv) → Space(2)
#
# Entity creation rejects:
# - create_point → raises ValueError
# - create_line non‑origin → raises ValueError
# - create_plane non‑origin → raises ValueError
# - create_sphere → raises ValueError
# - create_circle → raises ValueError
# - create_point_pair → raises ValueError
# - create_homogeneous_point → raises ValueError
#
# Operator round‑trips:
# - Rotor: create_rotor(π/2, Dir(0,0,1)) → MV → analyze_operator(mv) → Rotor(π/2, Dir(0,0,1))
# - ReflectionLine: create_reflection_line(Dir(1,0,0)) → MV → analyze_operator(mv) → ReflectionLine
# - ReflectionPlane: create_reflection_plane(Dir(0,1,0)) → MV → analyze_operator(mv) → ReflectionPlane
#
# Operator rejects:
# - create_translator → raises ValueError
# - create_dilator → raises ValueError
# - create_reflection_origin → raises ValueError
# - etc.
#
# Combined dispatcher:
# - Geometry(E2).create(entity) → MV
# - Geometry(E2).which_entity(mv) → entity
# - Geometry(E2).which_operator(mv) → operator
```

### `py/tests/test_geometry_p2.py` — P2 Round‑Trip Tests

```python
# Entity round‑trips:
# - Point: create_point(5, 3, 0) → MV → analyze_entity(mv) → Point(5, 3, 0)
# - Direction: create_direction(1, 0, 0) → MV → analyze_entity(mv) → Direction(1, 0, 0)
# - Line: create_line(Point(1,1,0), Dir(2,0,0)) → MV → analyze_entity(mv) → Line
# - Plane (line in 2D): create_plane(Plane(Point(0,0,0), Dir(0,1,0))) → MV → analyze_entity(mv) → Plane
# - Space: create_space(scale=3) → MV → analyze_entity(mv) → Space(3)
#
# Operator round‑trips:
# - Rotor: create_rotor(0.5, Dir(0,0,1)) → MV → analyze_operator(mv) → Rotor(0.5, Dir(0,0,1))
# - ReflectionLine: create_reflection_line(Dir(1,0,0)) → MV → analyze_operator(mv) → ReflectionLine
# - ReflectionPlane: create_reflection_plane(Dir(0,1,0)) → MV → analyze_operator(mv) → ReflectionPlane
# - ReflectionOrigin: create_reflection_origin() → MV → analyze_operator(mv) → ReflectionOrigin
#
# Combined dispatcher:
# - analyze(mv, opns=True) → Entity (fallback to operator if entity fails)
# - create.create_entity(basis, entity) → MV
# - create.create_operator(basis, operator) → MV
# - create.create(basis, obj) → MV
```

### `py/tests/test_geometry_n2.py` — N2 Round‑Trip Tests

```python
# Entity round‑trips:
# - Point: create_point(2, 3, 0) → MV → analyze_entity(mv) → Point(2, 3, 0)
# - Direction: create_direction(1, 0, 0) → MV → analyze_entity(mv) → Direction(1, 0, 0)
# - PointPair: create_point_pair(Point(0,0,0), Point(1,0,0)) → MV → analyze_entity(mv) → PointPair
# - Line: create_line(Point(0,0,0), Dir(1,1,0)) → MV → analyze_entity(mv) → Line
# - Plane (line in 2D): create_plane(Plane(Point(2,0,0), Dir(1,0,0))) → MV → analyze_entity(mv) → Plane
# - Circle: create_circle(Point(0,0,0), Dir(0,0,1), 3) → MV → analyze_entity(mv) → Circle
# - Sphere (circle in 2D): create_sphere(Point(1,1,0), 2) → MV → analyze_entity(mv) → Sphere
# - Space: create_space(scale=1) → MV → analyze_entity(mv) → Space(1)
#
# OPNS/IPNS toggle:
# - Point IPNS: create_point(2,3,0, opns=False) → dual → round‑trip to Point
# - Sphere IPNS: create_sphere(Point(0,0,0), 3, opns=False) → MV → analyze → Sphere
#
# Operator round‑trips:
# - Rotor: create_rotor(0.7, Dir(0,0,1)) → MV → analyze_operator(mv) → Rotor(0.7, Dir(0,0,1))
# - Translator: create_translator(1, 2) → MV → analyze_operator(mv) → Translator
# - Dilator: create_dilator(2) → MV → analyze_operator(mv) → Dilator
# - Motor: create_motor(Rotor(0.5, Dir(0,0,1)), Translator(1,0,0))
#   → MV → analyze_operator(mv) → Motor
# - ReflectionLine: create_reflection_line(Dir(1,0,0)) → MV → analyze_operator(mv) → ReflectionLine
# - ReflectionPlane: create_reflection_plane(Dir(0,1,0)) → MV → analyze_operator(mv) → ReflectionPlane
# - ReflectionOrigin: create_reflection_origin() → MV → analyze_operator(mv) → ReflectionOrigin
# - Inversion: create_inversion(Point(0,0,0), 1) → MV → analyze_operator(mv) → Inversion
# - GeneralRotor: create_general_rotor(Rotor(0.5, Dir(0,0,1)), Translator(1,0,0))
#   → MV → analyze_operator(mv) → GeneralRotor
# - GeneralDilator: create_general_dilator(2, Translator(1,0,0))
#   → MV → analyze_operator(mv) → GeneralDilator
#
# Null cone property:
# - Point OPNS: sp(p, rev(p)) ≈ 0 (points lie on null cone)
# - einf² = 0, eo² = 0, einf·eo = -1
```

### `py/tests/test_geometry_pga2.py` — PGA2 Round‑Trip Tests

```python
# Entity round‑trips:
# - Point: create_point(1, 2, 0) → MV → analyze_entity(mv) → Point(1, 2, 0)
# - Direction: create_direction(1, 0, 0) → MV → analyze_entity(mv) → Direction(1, 0, 0)
# - Plane (line in 2D): create_plane(Plane(Point(0,0,0), Dir(1,0,0))) → MV → analyze_entity(mv) → Plane
# - Line: create_line(Point(1,1,0), Dir(2,0,0)) → MV → analyze_entity(mv) → Line
# - Space: create_space(scale=1) → MV → analyze_entity(mv) → Space(1)
#
# OPNS/IPNS:
# - Point IPNS: create_point(1,2,0, opns=False) → MV → dual → IPNS form
# - Plane OPNS/IPNS round‑trip
#
# Operator round‑trips:
# - Rotor: create_rotor(0.3, Dir(0,0,1)) → MV → analyze_operator(mv) → Rotor(0.3, Dir(0,0,1))
# - Translator: create_translator(2, 3) → MV → analyze_operator(mv) → Translator
# - Motor: create_motor(Rotor(0.4, Dir(0,0,1)), Translator(1,0,0))
#   → MV → analyze_operator(mv) → Motor
# - ReflectionLine: create_reflection_line(Dir(1,0,0)) → MV → analyze_operator(mv) → ReflectionLine
# - ReflectionPlane: create_reflection_plane(Dir(0,1,0)) → MV → analyze_operator(mv) → ReflectionPlane
# - ReflectionOrigin: create_reflection_origin() → MV → analyze_operator(mv) → ReflectionOrigin
# - GeneralRotor: create_general_rotor(Rotor(0.5, Dir(0,0,1)), Translator(1,0,0))
#   → MV → analyze_operator(mv) → GeneralRotor
#
# Algebra detection:
# - Algebra.from_name("PGA2") detected as "pga2" (not "n2")
# - BasisPGA2 is instance of BasisN2 but analyze dispatches to PGA2
```

### `py/tests/test_viz_2d.py` — 2D Visualization Integration Tests

```python
# Visualizer construction:
# - Visualizer(space_dim=2) creates with correct SceneConfig
# - Title defaults to "Tanga 2D Viewer" when space_dim=2
# - Custom title is preserved when space_dim=2
# - SceneConfig.to_dict() includes "space_dim": 2
#
# Entity add + serialize:
# - viz.add(Point(3, 4, 0)) returns entity_id
# - Entity serializes with z=0: {"position": [3, 4, 0]}
# - viz.add(Direction(1, 0, 0)) returns entity_id
# - viz.add(Line(Point(0,0,0), Direction(1,0,0))) returns entity_id
#
# MV resolution:
# - viz.add(e2_basis.vector(3, 4)) → resolves via analyze → Direction(3, 4, 0)
# - viz.add(n2_basis.point(3, 4, 0)) → resolves via analyze → Point(3, 4, 0)
#
# Multi‑scene:
# - viz.scene("sub").config.space_dim == 2 (inherits from visualizer)
#
# FigureConfig:
# - FigureConfig(space_dim=2).to_dict() includes "space_dim": 2
#
# VisualizerApp:
# - MyApp(space_dim=2) forwards space_dim to Visualizer
```

## Implementation Checklist

- [ ] 7.1  Create `py/tests/test_basis_2d.py` — basis class smoke tests
- [ ] 7.2  Create `py/tests/test_geometry_e2.py` — E2 round‑trip tests
- [ ] 7.3  Create `py/tests/test_geometry_p2.py` — P2 round‑trip tests
- [ ] 7.4  Create `py/tests/test_geometry_n2.py` — N2 round‑trip tests
- [ ] 7.5  Create `py/tests/test_geometry_pga2.py` — PGA2 round‑trip tests
- [ ] 7.6  Create `py/tests/test_viz_2d.py` — 2D visualization integration tests
- [ ] 7.7  Run `pytest py/tests/ -k "e2 or p2 or n2 or pga2 or basis_2d or viz_2d"` — all pass