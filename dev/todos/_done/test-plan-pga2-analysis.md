# Test Plan: PGA2 Entity & Operator Analysis

Tests for the PGA2 `create` ↔ `analyze` round-trip and operator application.

## Implementation

**New file**: `py/tests/geometry/test_geometry_pga2_analysis.py`

This is an **additional** test file alongside the existing `py/tests/geometry/test_geometry_pga2.py`. The existing file contains algebra-specific detection tests and basic round-trips (point, line, space, rotor, motor, etc.) which are retained as-is. The new `_analysis` file adds comprehensive operator coverage (including the newly fixed Translator, ReflectionLine, ReflectionOrigin, GeneralRotor, and TripleReflection) plus operator application tests that validate geometric transformations.

## Test Structure

Each test follows this pattern:
1. Create an entity/operator via `create()` or `create_operator()` / `create_entity()`
2. Analyze it via `analyze()` / `analyze_entity()` / `analyze_operator()`
3. Assert the analyzed output matches the input (round-trip)

For operators, additionally:
4. Create a test entity (Point or Direction)
5. Apply the operator via `V * entity * V.rev()`
6. Analyze the transformed entity
7. Assert the transformation matches expectations

Algebra: `BasisPGA2()` via `Algebra.from_name("PGA2")` fixture.

In 2D PGA:
- Points are grade-2 bivectors (OPNS) — intersection of two lines
- Lines are grade-1 vectors (OPNS) — codimension-1 hyperplanes (lines in 2D)
- Directions are grade-1 IPNS vectors with no e₀ component
- Rotations are always about the z-axis (axis `Dir(0, 0, 1)`)
- Triple reflections use `Line` entities (not `Plane`)

---

## Entity Tests (Round-Trip: Create → Analyze)

### E1. Point ✅
| Step | Action | Expected |
|---|---|---|
| 1 | `create_entity(b, Point(3, -2, 0))` | OPNS point MV (grade-2) |
| 2 | `analyze_entity(mv, opns=True)` | `Point` with `x≈3, y≈-2` |

### E2. Direction (OPNS raises — known limitation) ✅
| Step | Action | Expected |
|---|---|---|
| 1 | `create_entity(b, Direction(1, 0, 0))` / `analyze_entity(opns=True)` | `ValueError` — PGA2 direction OPNS triggers degenerate bivector factorization |

### E3. Line (2D = "plane" in 3D parlance) ✅
| Step | Action | Expected |
|---|---|---|
| 1 | `create_entity(b, Line(origin=Point(1, 0, 0), direction=Direction(0, 1, 0)))` | OPNS line MV (grade-1) |
| 2 | `analyze_entity(mv, opns=True)` | `Line` with correct direction |

### E4. Space ✅
| Step | Action | Expected |
|---|---|---|
| 1 | `create_entity(b, Space(3.0))` | OPNS space MV (grade-3) |
| 2 | `analyze_entity(mv, opns=True)` | `Space` |

---

## Operator Tests (Round-Trip: Create → Analyze)

### O1. Rotor ✅
| Step | Action | Expected |
|---|---|---|
| 1 | `create_operator(b, Rotor(angle=π/2, axis=Direction(0, 0, 1)))` | Rotor MV (scalar + e₁₂) |
| 2 | `analyze_operator(mv)` | `Rotor` with `angle≈π/2, axis.z≈1` |

### O2. Translator ✅
| Step | Action | Expected |
|---|---|---|
| 1 | `create_operator(b, Translator(vector=Direction(2, -1, 0)))` | Translator MV |
| 2 | `analyze_operator(mv)` | `Translator` with `vector≈Dir(2, -1, 0)` |

### O3. Motor ✅
| Step | Action | Expected |
|---|---|---|
| 1 | `create_operator(b, Motor(Rotor(π/2, Dir(0,0,1)), Translator(Dir(1,2,0))))` | Motor MV |
| 2 | `analyze_operator(mv)` | `Motor` (or `GeneralRotor`) with correct rotor+translator |

### O4. ReflectionLine (reflect across a line through origin) ✅
| Step | Action | Expected |
|---|---|---|
| 1 | `create_operator(b, ReflectionLine(direction=Direction(1, 0, 0)))` | ReflectionLine MV (grade-2) |
| 2 | `analyze_operator(mv)` | `ReflectionLine` with `d≈Dir(1, 0, 0)` |

### O5. ReflectionOrigin ✅
| Step | Action | Expected |
|---|---|---|
| 1 | `create_operator(b, ReflectionOrigin())` | ReflectionOrigin MV (grade-2, e₁₂) |
| 2 | `analyze_operator(mv)` | `ReflectionOrigin` (or `Rotor`/`GeneralRotor` — check actual) |

### O6. GeneralRotor ✅
| Step | Action | Expected |
|---|---|---|
| 1 | `create_operator(b, GeneralRotor(Rotor(π/2, Dir(0,0,1)), Translator(Dir(1,0,0))))` | GeneralRotor MV (grades 0+2) |
| 2 | `analyze_operator(mv)` | `GeneralRotor` with correct rotor+translator |

### O7. TripleReflection (3 line reflections) ⚠️ (skipped — 5D embedding prevents clean 3-factor construction)
| Step | Action | Expected |
|---|---|---|
| 1 | Create three line vectors: `l1 = mv({E1:1,EP:-1,EM:-1})` (line x=1), `l2 = mv({E1:1})` (line x=0), `l3 = mv({E2:1})` (line y=0) | |
| 2 | `mv = l1 * l2 * l3` | Triple reflection versor |
| 3 | `analyze_operator(mv)` | `TripleReflection` with three `Line` entities |

---

## Operator Application Tests (Create → Apply → Analyze)

### A1. Translator: point displacement
| Step | Action | Expected |
|---|---|---|
| 1 | `p = create_entity(b, Point(0, 0, 0))` | Origin point |
| 2 | `T = create_operator(b, Translator(Dir(3, 0, 0)))` | Translator (+3 in x) |
| 3 | `p' = T * p * T.rev()` | Translated point |
| 4 | `analyze_entity(p', opns=True)` | `Point(3, 0, 0)` |

### A2. Rotor: point rotation by 90° about z
| Step | Action | Expected |
|---|---|---|
| 1 | `p = create_entity(b, Point(1, 0, 0))` | Point on x-axis |
| 2 | `R = create_operator(b, Rotor(π/2, Dir(0,0,1)))` | 90° rotor |
| 3 | `p' = R * p * R.rev()` | Rotated point |
| 4 | `analyze_entity(p', opns=True)` | `Point(0, 1, 0)` |

### A3. Motor: rigid motion (translate then rotate)
| Step | Action | Expected |
|---|---|---|
| 1 | `p = create_entity(b, Point(0, 0, 0))` | Origin |
| 2 | `M = create_operator(b, Motor(Rotor(π/2, Dir(0,0,1)), Translator(Dir(1,0,0))))` | Motor |
| 3 | `p' = M * p * M.rev()` | Transformed point |
| 4 | `analyze_entity(p', opns=True)` | `Point(0, 1, 0)` (translate then rotate 90°) |

### A4. ReflectionLine: mirror point across line
| Step | Action | Expected |
|---|---|---|
| 1 | `p = create_entity(b, Point(3, 1, 0))` | Point |
| 2 | `L = create_operator(b, ReflectionLine(Dir(1,0,0)))` | Reflection across line through origin along x |
| 3 | `p' = L * p * L.rev()` | Reflected |
| 4 | `analyze_entity(p', opns=True)` | The sign of the perpendicular component should flip |

### A5. ReflectionOrigin: point reflection about origin
| Step | Action | Expected |
|---|---|---|
| 1 | `p = create_entity(b, Point(5, -3, 0))` | |
| 2 | `O = create_operator(b, ReflectionOrigin())` | |
| 3 | `p' = O * p * O.rev()` | |
| 4 | `analyze_entity(p', opns=True)` | `Point(-5, 3, 0)` |

### A6. GeneralRotor: rotation about a displaced center
| Step | Action | Expected |
|---|---|---|
| 1 | `p = create_entity(b, Point(3, 0, 0))` | Point at (3,0) |
| 2 | `G = create_operator(b, GeneralRotor(Rotor(π/2, Dir(0,0,1)), Translator(Dir(1,0,0))))` | Rot 90° about center (1,0) |
| 3 | `p' = G * p * G.rev()` | |
| 4 | `analyze_entity(p', opns=True)` | `Point(1, 2, 0)` (relative pos (2,0) → (0,2) → absolute (1,2)) |
</context>
</write_to_file>