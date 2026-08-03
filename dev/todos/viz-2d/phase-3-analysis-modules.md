# Phase 3 — Analysis Modules

MV → entity/operator dataclass recognition for each 2D algebra. Follow the
pattern of `analysis_e3.py` with 2D‑specific grade mappings.

## Entity Grade Mapping (2D OPNS)

| Algebra | Point | Line | Plane | Circle | Sphere | Space | Direction | PointPair |
|---------|-------|------|-------|--------|--------|-------|-----------|-----------|
| E2 | — | grade‑1 | grade‑1 (dual) | — | — | grade‑2 | grade‑1 (same as line) | — |
| P2 | grade‑2 | grade‑2 | grade‑1 | — | — | grade‑3 | grade‑1 (ideal, no e₃) | — |
| N2 | grade‑1 | grade‑3 | grade‑1 (IPNS), grade‑4 (OPNS) | grade‑2 (IPNS), grade‑3 (OPNS) | grade‑1 (IPNS), grade‑3 (OPNS) | grade‑4 | grade‑1 (no e₀/e∞) | grade‑2 |
| PGA2 | grade‑3 (OPNS) | grade‑2 | grade‑1 | — | — | grade‑3 | grade‑1 (no e₀) | — |

## Files to Create

### `py/pytanga/geometry/analysis_e2.py`

Entity analysis from grade of the MV blade (OPNS or IPNS).

**OPNS entities:**
- Grade 0 → scalar → raise ValueError
- Grade 1 → `Direction` (line through origin in E2)
- Grade 2 → `Space` (bivector e12 = pseudoscalar)

**IPNS entities:**
- Grade 0 → raise ValueError
- Grade 1 → `Plane` through origin (normal = vector) — a 2D plane = a line
- Grade 2 → `Line` through origin (intersection of two planes/lines) → raises? Actually in E2 IPNS, grade 2 would be a point at origin — but E2 can't represent points. Raise ValueError.

**Operator analysis:**
- Pure grade 1 → `ReflectionLine(direction)`
- Pure grade 2 → `ReflectionPlane(normal)` — a bivector bounce = rotation by 2× angle
- Two‑grade versor (scalar + bivector) → `Rotor(angle, axis)` — axis is always (0,0,1) in 2D
  - Interpret as: `cos(θ/2) + sin(θ/2)·ω·e12`, where ω·e12 encodes the bivector.
  - Rotation angle = 2·acos(cos(θ/2)), computed from scalar part
  - Axis = Direction(0, 0, 1) (the plane of rotation is the only plane in 2D)

### `py/pytanga/geometry/analysis_p2.py`

**OPNS entities:**
- Grade 1 → `Direction` (no e₃ component) or `Plane` (has e₃ component)
- Grade 2 → `Point` (intersection of two planes) or `Line` (intersection of plane + direction)
  - Need `BladeFactorize` or a geometric test to disambiguate
- Grade 3 → `Space` (e123)

**IPNS entities:**
- Grade 1 → `Plane` (line in 2D), `Direction` (no e₃, ideal plane at infinity)
- Grade 2 → `Line` (intersection of two planes = a point? No — in P2, intersection of two lines=point)
- Grade 3 → `Point` (intersection of three planes; only the trivial origin)

**Operator analysis:**
- Same as E3 but with 2D bivector only: `ReflectionLine`, `ReflectionPlane`, `ReflectionOrigin`, `Rotor`

### `py/pytanga/geometry/analysis_n2.py`

Mirrors `analysis_n3.py` with 2D‑specific grades.

**OPNS entities:**
- Grade 1 → `Point` (COP on null cone) or `Direction` (no e₀/e∞)
- Grade 2 → `PointPair` or `Circle` (IPNS `S∧P`)
- Grade 3 → `Circle` (OPNS) or `Line` (OPNS `Cop∧Cop∧ei`)
- Grade 4 → `Sphere` (OPNS, dual of IPNS sphere) or `Space`

**IPNS support** via dualize → OPNS → analyze.

**Operator analysis:**
- `ReflectionLine`, `ReflectionPlane`, `ReflectionOrigin`, `Inversion`,
  `Rotor`, `Translator`, `Dilator`, `Motor`, `GeneralRotor`, `GeneralDilator`

### `py/pytanga/geometry/analysis_pga2.py`

Mirrors `analysis_pga3.py` with 2D grades.

**OPNS entities:**
- Grade 1 → `Plane` (line in 2D)
- Grade 2 → `Line` (point in 2D — intersection of two lines) or `ReflectionLine`
- Grade 3 → `Point` (intersection of three planes) or `Space`

**Operator analysis:**
- `ReflectionLine`, `ReflectionPlane`, `ReflectionOrigin`, `Rotor`,
  `Translator`, `Motor`, `GeneralRotor`

## Implementation Checklist

- [ ] 3.1  Create `py/pytanga/geometry/analysis_e2.py` — E2 entity + operator analysis
- [ ] 3.2  Create `py/pytanga/geometry/analysis_p2.py` — P2 entity + operator analysis
- [ ] 3.3  Create `py/pytanga/geometry/analysis_n2.py` — N2 entity + operator analysis
- [ ] 3.4  Create `py/pytanga/geometry/analysis_pga2.py` — PGA2 entity + operator analysis
- [ ] 3.5  Verify E2 round‑trip: `create_e2.create_direction(b, 3,4,0)` → `analysis_e2.analyze_entity(mv)` → `Direction(3,4,0)`
- [ ] 3.6  Verify E2 rotor round‑trip: `create_e2.create_rotor(b, π/2, Dir(0,0,1))` → `analysis_e2.analyze_operator(mv)` → `Rotor(angle=π/2, axis=Dir(0,0,1))`
- [ ] 3.7  Verify P2 point round‑trip: `create_p2.create_point(b, 5,3,0)` → `analyze_entity(mv)` → `Point(5,3,0)`
- [ ] 3.8  Verify N2 point round‑trip: `create_n2.create_point(b, 2,3,0)` → `analyze_entity(mv)` → `Point(2,3,0)`
- [ ] 3.9  Verify N2 sphere round‑trip: `create_n2.create_sphere(b, Point(1,1,0), 2)` → `analyze_entity(mv)` → `Sphere(Point(1,1,0), 2)`
- [ ] 3.10 Verify PGA2 point round‑trip: `create_pga2.create_point(b, 1,2,0)` → `analyze_entity(mv)` → `Point(1,2,0)`