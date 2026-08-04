# Phase 7 — Tests (Step‑wise Implementation)

Each step produces **one** test file, runs it, fixes issues, and commits
before moving to the next step.  This keeps each batch small and verifiable.

All tests go under `py/tests/`.  Use `pytest` as the test framework.

---

## Step 7.1 — Basis Class Smoke Tests

**File:** `py/tests/test_basis_2d.py`

Minimal smoke tests that verify the algebra plumbing is wired correctly.
No geometry round‑trips — just instantiation and basic blade properties.

### Tests to write

```python
# - Algebra.from_name("E2") returns BasisE2 instance
# - Algebra.from_name("P2") returns BasisP2 instance
# - Algebra.from_name("N2") returns BasisN2 instance
# - Algebra.from_name("PGA2") returns BasisPGA2 instance
# - E2: e1 * e2 == e12
# - P2: point(3, 4) yields e3=1 component (homogeneous point)
# - N2: einf² = 0, eo² = 0, einf·eo = −1
# - PGA2: e0² = 0 (null vector)
# - PGA2 is recognized before N2 in isinstance checks
# - Each basis: algebra_dim matches 2^dim
```

### Commands

```bash
pytest py/tests/test_basis_2d.py -v
```

**Commit after passing.**

---

## Step 7.2 — E2 Round‑Trip Tests

**File:** `py/tests/geometry/test_geometry_e2.py`

Mirrors `test_geometry_e3.py` with 2D blade IDs and entities.

### Tests to write

#### Entity round‑trips
```python
# - Direction: create_entity(basis, Dir(3,4,0)) → analyze → Direction(3,4,0)
# - Line through origin: create_entity(basis, Line(Pt(0,0,0), Dir(1,0,0)))
#   → analyze → Direction or Line (E2 can't distinguish line from direction)
# - Space: create_entity(basis, Space(2)) → analyze → Space(2)
```

#### Entity creation rejects
```python
# - create_point → raises ValueError
# - create_line non‑origin → raises ValueError
# - create_sphere → raises ValueError
# - create_circle → raises ValueError
# - create_point_pair → raises ValueError
# - create_homogeneous_point → raises ValueError
```

#### Operator round‑trips
```python
# - Rotor: create_operator(basis, Rotor(π/2, Dir(0,0,1))) → MV
#   → analyze_operator → Rotor(π/2, Dir(0,0,1))
# - ReflectionLine: create → analyze → ReflectionLine
```

#### Operator creation rejects
```python
# - create_translator → raises ValueError
# - create_dilator → raises ValueError
# - create_reflection_origin → raises ValueError
# - create_inversion → raises ValueError
# - create_motor → raises ValueError
```

#### Combined dispatcher
```python
# - create(basis, Direction(1,0,0)) → MV
# - create(basis, Rotor(0.5, Dir(0,0,1))) → MV
```

### Commands

```bash
pytest py/tests/geometry/test_geometry_e2.py -v
```

**Commit after passing.**

---

## Step 7.3 — P2 Round‑Trip Tests

**File:** `py/tests/geometry/test_geometry_p2.py`

Mirrors `test_geometry_p3.py` with 2D blade IDs (E3 = homogeneous dimension).

### Tests to write

#### Entity round‑trips (OPNS)
```python
# - Point: create_entity(basis, Pt(5,3,0)) → analyze → Pt(5,3,0)
# - Direction: create_entity(basis, Dir(1,0,0)) → analyze → Dir(1,0,0)
# - Line: create_entity(basis, Line(Pt(1,1,0), Dir(2,0,0)))
#   → analyze → Line (direction matches, origin may differ due to orthogonalization)
# - Plane: create_entity(basis, Plane(Pt(0,0,0), Dir(0,1,0)))
#   → analyze → Plane (in 2D, a plane is a line)
# - Space: create_entity(basis, Space(3)) → analyze → Space(3)
```

#### Entity round‑trips (IPNS)
```python
# - Point IPNS: create_entity(basis, Pt(1,2,0), opns=False) → grade 3 → analyze IPNS → Pt(1,2,0)
# - Direction IPNS: create_entity(basis, Dir(1,0,0), opns=False) → grade 3 → analyze IPNS → Dir(1,0,0)
# - Line IPNS: create_entity(basis, Line(...), opns=False) → grade 2 → analyze IPNS → Line
# - Space IPNS: create_entity(basis, Space(3), opns=False) → grade 0 → analyze IPNS → Space(3)
```

#### N3 entity rejects
```python
# - Sphere, Circle, PointPair, HPoint → raises ValueError matching "N3"
```

#### Operator round‑trips
```python
# - Rotor: create → analyze → Rotor(angle, axis=Dir(0,0,1))
# - ReflectionLine (grade 2 bivector with e₃): create → analyze → ReflectionLine
# - ReflectionOrigin (grade 1, only e₃): create → analyze → ReflectionOrigin
```

#### Operator creation rejects
```python
# - Translator, Dilator, Inversion, Motor → raises ValueError matching "N3"
```

#### Operator applications
```python
# - ReflectionLine application on Hop(a) → flips perpendicular components
# - ReflectionOrigin: e₃·Hop(a)·e₃ → projects to −a
# - Rotor application: R·Hop(a)·R̃ → Hop(R(a))
```

#### Combined dispatcher
```python
# - create(basis, entity) → MV
# - create(basis, operator) → MV
```

### Commands

```bash
pytest py/tests/geometry/test_geometry_p2.py -v
```

**Commit after passing.**

---

## Step 7.4 — N2 Round‑Trip Tests

**File:** `py/tests/geometry/test_geometry_n2.py`

Mirrors `test_geometry_n3.py` with 2D blade IDs.  The N2 module is the
most complex — covers all conformal entities and operators in 2D.

### Tests to write

#### Entity create‑analyze round‑trips
```python
# - Point: create(basis, Pt(2,3,0)) → analyze OPNS → Pt(2,3,0)
# - Direction: create(basis, Dir(1,0,0)) → analyze OPNS → Dir(1,0,0)
# - PointPair: create(basis, PtPair(Pt(0,0,0), Pt(1,0,0)))
#   → analyze OPNS → PtPair
# - Line: create(basis, Line(Pt(0,0,0), Dir(1,1,0)))
#   → analyze OPNS → Line (origin and dir extracted from blade components)
# - Circle (sphere in 2D): create_entity(basis, Sphere(Pt(1,1,0), 2))
#   → analyze OPNS → Sphere (circle)
# - Circle via create_circle: delegates to create_sphere
# - Space: create(basis, Space(1)) → analyze → Space(1)
# - HPoint: create(basis, HPoint(Pt(1,2,0))) → analyze → HPoint
```

#### OPNS/IPNS toggle
```python
# - Point IPNS: create_entity(basis, Pt(2,3,0), opns=False)
#   → analyze IPNS → Pt(2,3,0)
# - Sphere (circle) IPNS: create_entity(basis, Sphere(Pt(0,0,0), 3), opns=False)
#   → analyze IPNS → Sphere
```

#### Null cone property
```python
# - Point OPNS: sp(p, rev(p)) ≈ 0 (points lie on null cone)
# - einf² = 0, eo² = 0, einf·eo = −1
# - Inner product distance: sp(Cop(0,0), Cop(3,0)) ≈ −4.5 (= −½‖3‖²)
```

#### Operator create‑analyze round‑trips
```python
# - Rotor: create(basis, Rotor(0.7, Dir(0,0,1))) → analyze → Rotor(0.7, Dir(0,0,1))
# - Translator: create(basis, Translator(Dir(1,2,0))) → analyze → Translator
#   (vector components match)
# - Dilator: create(basis, Dilator(2)) → analyze → Dilator(2)
# - Motor: create(basis, Motor(Rotor(0.5, Dir(0,0,1)), Translator(Dir(1,0,0))))
#   → analyze → Motor
# - ReflectionLine: create(basis, RefLine(Dir(1,0,0))) → analyze → RefLine
# - ReflectionOrigin: create(basis, RefOrigin()) → analyze → RefOrigin
# - Inversion: create(basis, Inversion(Pt(0,0,0), 1)) → analyze → Inversion
# - GeneralRotor: create(basis, GeneralRotor(Rotor(0.5, ...), Translator(...)))
#   → analyze → GeneralRotor
# - GeneralDilator: create(basis, GeneralDilator(2, Translator(...)))
#   → analyze → GeneralDilator
```

#### Operator applications
```python
# - Translator: T·Cop(1,2)·T̃ with T = Translator(Dir(10,0))
#   → Cop(11,2) → Point(11,2,0) (round‑trip)
# - Inversion: I·Cop(2,0)·Ĩ with I = Inversion(Pt(0,0,0), 1)
#   → Point(0.5, 0, 0)
# - Dilator round‑trip with factor 0.5 → Dilator(factor=0.5)
# - GeneralRotor application: G·Cop(0,0)·G̃ with translation to (10,0)
#   and 90° rotation → Point(10,10,0)
# - GeneralDilator at (1,0) with factor 2:
#   G·Cop(2,0)·G̃ → Point(3,0,0)
```

#### Imaginary entities
```python
# - Imag sphere (circle) IPNS: S² = −r²
# - Imag sphere OPNS round‑trip → Sphere(is_imaginary=True)
```

### Commands

```bash
pytest py/tests/geometry/test_geometry_n2.py -v
```

**Commit after passing.**

---

## Step 7.5 — PGA2 Round‑Trip Tests

**File:** `py/tests/geometry/test_geometry_pga2.py`

Tests the Gunn/Dorst plane‑based PGA model in 2D (4D algebra with null
e₀ = ep + em embedding).

### Tests to write

#### Entity create‑analyze round‑trips
```python
# - Point OPNS: create_entity(basis, Pt(1,2,0)) → analyze → Pt(1,2,0)
# - Direction OPNS: create_entity(basis, Dir(1,0,0)) → analyze → Dir(1,0,0)
# - Line: create_entity(basis, Line(Pt(0,0,0), Dir(1,0,0)))
#   → analyze → Line (grade‑1 vector, codimension‑1 hyperplane)
# - Space: create_entity(basis, Space(1)) → analyze → Space(1)
```

#### OPNS/IPNS
```python
# - Point IPNS: create_entity(basis, Pt(1,2,0), opns=False)
#   → analyze IPNS → Pt(1,2,0)
```

#### Operator create‑analyze round‑trips
```python
# - Rotor: create(basis, Rotor(0.3, Dir(0,0,1))) → analyze → Rotor(0.3, Dir(0,0,1))
# - Translator: create(basis, Translator(Dir(2,3))) → analyze → Translator
# - Motor: create(basis, Motor(Rotor(0.4, ...), Translator(...)))
#   → analyze → Motor
# - ReflectionLine (bivector d∧e₀): create → analyze → RefLine
# - ReflectionOrigin (bivector e₁∧e₂): create → analyze → RefOrigin
# - GeneralRotor: create(basis, GenRotor(Rotor(0.5, ...), Translator(...)))
#   → analyze → GeneralRotor
```

#### Operator applications
```python
# - Translator: T·P·T̃ (translate a point)
# - Rotor: R·L·R̃ (rotate a line around origin)
# - Motor: M·P·M̃ (rotate + translate a point in one go)
# - GeneralRotor: G·P·G̃ (rotate about a displaced point)
```

#### Algebra detection
```python
# - Algebra.from_name("PGA2") detected as "pga2" (not "n2")
# - BasisPGA2 is instance of BasisN2 but analyze dispatches to PGA2
```

### Commands

```bash
pytest py/tests/geometry/test_geometry_pga2.py -v
```

**Commit after passing.**

---

## Step 7.6 — 2D Visualization Integration Tests

**File:** `py/tests/viz/test_viz_2d.py`

Tests the visualizer pipeline with `space_dim=2`.

### Tests to write

#### Visualizer construction
```python
# - Visualizer(space_dim=2) creates with correct SceneConfig
# - Title defaults to "Tanga 2D Viewer" when space_dim=2
# - Custom title is preserved when space_dim=2
# - SceneConfig.to_dict() includes "space_dim": 2
```

#### Entity add + serialize
```python
# - viz.add(Point(3, 4, 0)) returns entity_id
# - Entity serializes with z=0: {"position": [3, 4, 0]}
# - viz.add(Direction(1, 0, 0)) returns entity_id
# - viz.add(Line(Pt(0,0,0), Dir(1,0,0))) returns entity_id
```

#### Multi‑scene
```python
# - viz.scene("sub").config.space_dim == 2 (inherits from visualizer)
```

#### FigureConfig
```python
# - FigureConfig(space_dim=2).to_dict() includes "space_dim": 2
```

#### VisualizerApp
```python
# - VisualizerApp(space_dim=2) forwards space_dim to Visualizer
```

### Commands

```bash
pytest py/tests/viz/test_viz_2d.py -v
```

**Commit after passing.**

---

## Step 7.7 — Full Suite Run

Run all 2D‑related tests together to confirm no cross‑test interference.

```bash
pytest py/tests/test_basis_2d.py py/tests/geometry/test_geometry_e2.py py/tests/geometry/test_geometry_p2.py py/tests/geometry/test_geometry_n2.py py/tests/geometry/test_geometry_pga2.py py/tests/viz/test_viz_2d.py -v
```

Also ensure the existing 3D tests still pass (regression check):

```bash
pytest py/tests/ -x --ignore=py/tests/test_basis_2d.py --ignore=py/tests/geometry/test_geometry_e2.py --ignore=py/tests/geometry/test_geometry_p2.py --ignore=py/tests/geometry/test_geometry_n2.py --ignore=py/tests/geometry/test_geometry_pga2.py --ignore=py/tests/viz/test_viz_2d.py
```

**Commit after passing.**

---

## Implementation Checklist

- [ ] 7.1  Create `py/tests/test_basis_2d.py` — basis class smoke tests → commit
- [ ] 7.2  Create `py/tests/geometry/test_geometry_e2.py` — E2 round‑trip tests → commit
- [ ] 7.3  Create `py/tests/geometry/test_geometry_p2.py` — P2 round‑trip tests → commit
- [ ] 7.4  Create `py/tests/geometry/test_geometry_n2.py` — N2 round‑trip tests → commit
- [ ] 7.5  Create `py/tests/geometry/test_geometry_pga2.py` — PGA2 round‑trip tests → commit
- [ ] 7.6  Create `py/tests/viz/test_viz_2d.py` — 2D viz integration tests → commit
- [ ] 7.7  Full suite run + 3D regression check → commit