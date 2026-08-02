# Geometry Fix — Overview Plan

## Scope

Audit and fix entity/operator creation and analysis in `py/pytanga/geometry/`
against the definitions in Christian Perwass's habilitation thesis
(*Geometric Algebra with Applications in Engineering*, Chapters on
E3, P3, N3 conformal space).

## Design Principle

**If an entity or operator cannot be represented in a given space, raise a
`ValueError` with an explanation — do NOT silently map it to something else
or approximate it.**

## Reference Documents

- `dev/todos/geo_fix/e3_entities.md` — E3 entities and operators (Perwass definitions)
- `dev/todos/geo_fix/p3_entities.md` — P3 entities and operators (Perwass definitions)
- `dev/todos/geo_fix/n3_entities.md` — N3 entities and operators (Perwass definitions)
- `dev/todos/geo_fix/phase2_fix_e3.md` — Phase 2 plan: fix E3
- `dev/todos/geo_fix/phase3_fix_p3.md` — Phase 3 plan: fix P3
- `dev/todos/geo_fix/phase4_fix_n3.md` — Phase 4 plan: fix N3
- `dev/todos/geo_fix/phase5_add_n3_entities.md` — Phase 5 plan: add missing N3 entities/operators

## Current Code Architecture

```
py/pytanga/geometry/
├── entities.py         # Dataclasses: Point, Direction, Line, Plane, Circle, Sphere, ...
├── operators.py        # Dataclasses: Reflection, Inversion, Rotor, Translator, Dilator, Motor, ...
├── create.py           # Dispatcher: create_entity(), create_operator(), create()
├── analysis.py         # Dispatcher: analyze_entity(), analyze_operator(), analyze()
├── create_e3.py        # E3 MV creation
├── create_p3.py        # P3 MV creation
├── create_n3.py        # N3 MV creation
├── create_pga3.py      # PGA3 MV creation (out of scope)
├── analysis_e3.py      # E3 MV → dataclass analysis
├── analysis_p3.py      # P3 MV → dataclass analysis
├── analysis_n3.py      # N3 MV → dataclass analysis
└── analysis_pga3.py    # PGA3 analysis (out of scope)
```

---

## Phases

### Phase 1 — Audit (COMPLETE) ✅

Created reference documents from Perwass thesis:
- ✅ `e3_entities.md` — extracted from `GAEucSpc.tex`
- ✅ `p3_entities.md` — extracted from `GAPrjSpc.tex`
- ✅ `n3_entities.md` — extracted from `GAConfSpc.tex`, `GAConfSpc_Rep.tex`, `GAConfSpc_Op.tex`, `GAConfSpc_Ana.tex`

Created detailed fix plans per space:
- ✅ `phase2_fix_e3.md` — entity/operator audit, specific fixes, test cases, implementation checklist
- ✅ `phase3_fix_p3.md` — entity/operator audit, specific fixes, test cases, implementation checklist
- ✅ `phase4_fix_n3.md` — entity/operator audit, specific fixes, test cases, implementation checklist
- ✅ `phase5_add_n3_entities.md` — missing entities/operators, implementation checklist

### Phase 2 — Fix E3 (COMPLETE) ✅

Implement fixes in `create_e3.py` and `analysis_e3.py`. Write tests for each entity creation and analysis function. Includes verifying rotor sign convention.

**Files**: `create_e3.py`, `analysis_e3.py`, `create.py` (dispatcher stubs), test files

**Plan**: See [phase2_fix_e3.md](phase2_fix_e3.md) for checklist.

### Phase 3 — Fix P3 (COMPLETE) ✅

Implement fixes in `create_p3.py` and `analysis_p3.py`. Write tests for each entity creation and analysis function. Includes fixing the reflection operator (must be bivector `N∧e₄`), adding direct IPNS plane creation, and adding N3-only exception stubs.

**Files**: `create_p3.py`, `analysis_p3.py`, `create.py` (dispatcher stubs), test files

**Plan**: See [phase3_fix_p3.md](phase3_fix_p3.md) for checklist.

### Phase 4 — Fix N3 (COMPLETE) ✅

Implement fixes in `create_n3.py` and `analysis_n3.py`. Write tests for each entity creation and analysis function. This is the largest phase: direct IPNS sphere/plane creation, fixing reflection/inversion/dilator operators, replacing factorization-based analysis with Perwass formulas, fixing translator blade IDs.

**Files**: `create_n3.py`, `analysis_n3.py`, `create.py` (dispatcher stubs), test files

**Plan**: See [phase4_fix_n3.md](phase4_fix_n3.md) for checklist.

### Phase 5 — Add Missing N3 Entities and Operators (COMPLETE) ✅

Implement entities and operators from Perwass that are not yet in the codebase. Includes: imag sphere, imag point pair, imag circle, circle with arbitrary normal, reflector, general rotor, general dilator, and motor convenience constructor.

**Files**: `create_n3.py`, `create_e3.py`, `create_p3.py`, `analysis_n3.py`, `entities.py`, `operators.py`, `create.py`, test files

**Plan**: See [phase5_add_n3_entities.md](phase5_add_n3_entities.md) for checklist.

### Phase 6 — Geometry Convenience Class (COMPLETE) ✅

Add a `Geometry` class that wraps an algebra instance with a default `opns`
flag.  Exposes `create()`, `which_entity()`, and `which_operator()` methods
that delegate to the existing dispatchers, always using the stored algebra.

**Files**: `_geometry.py` (new), `__init__.py`

**Plan**: See [phase6_geometry_class.md](phase6_geometry_class.md) for checklist.

---

## Cross-Cutting Concerns

### IPNS vs OPNS Architecture

The current code creates everything in OPNS and then dualizes for IPNS
(`if not opns: mv = mv.sdual()`). This should be replaced with a
**"simplest formula"** strategy:

- **Use whichever formula (IPNS or OPNS) gives the simplest, most precise
  algebraic construction**, then dualize if the caller wants the other
  null‑space representation.
- For N3: **sphere** (`S = A − ½ρ² e∞`, grade‑1 IPNS) and **plane**
  (`P = â + α e∞`, grade‑1 IPNS) are trivially simple one‑liners.
  Use the IPNS formula for *both* `opns=True` (dualize after IPNS
  construction) and `opns=False` (return IPNS directly).
- For P3: **plane** (`P = â − α·e₄`, grade‑1 IPNS) is similarly simple.
  Use IPNS formula for both `opns=True` and `opns=False`.
- For N3: **point pair** (`A∧B`, grade‑2 OPNS) is simpler than the
  3‑sphere intersection. Use OPNS formula, dualize for IPNS.
- For N3: **line**, **circle**, the OPNS and IPNS constructions have
  comparable complexity — both paths are acceptable. Prefer the one
  that avoids unnecessary point‑generation heuristics.
- OPNS creation should also use the IPNS formula if it is simpler and more precise, and the dualize. 

### Factorization-Based Analysis

The analysis code currently relies on `blade_factorize()` and `blade_factorize_versor()`. This is fragile (factor ordering, edge cases). Where Perwass provides explicit extraction formulas (notably for N3 sphere, plane, line, circle, point pair), those should be used instead.

### Blade ID Hardcoding

Blade IDs are hardcoded as integers. Must verify against the actual basis enumeration, especially for N3 translator and dilator components.

### Round‑Trip Fidelity

Creation and analysis must round‑trip: `analyze(create(X)) ≈ X` and
`create(analyze(blade)) ≈ blade` (up to global scale). This implies
that the creation formula and the analysis extraction formula **must
be inverses** of each other. Where Perwass provides explicit extraction
formulas (GAConfSpc_Ana.tex), the corresponding creation function must
use the algebraic inverse of that extraction.

### Sign Conventions

- Rotor: Perwass `R = cos(θ/2) - sin(θ/2)·N₂`, code `R = cos(θ/2) + sin(θ/2)·axis_bivector`. Must verify equivalence.
- Sphere IPNS: `S = A - ½ρ² e∞` (minus sign — critical)
- Translator: `T = 1 - ½ t e∞` (minus sign — critical)
- Dilator: Perwass `D = 1 + (1-d)/(1+d)·e∞∧e₀`, code uses opposite sign

---

## Files to Modify (Summary)

| File | Phase | Changes |
|------|-------|---------|
| `operators.py` | 2-3 | Split `Reflection` → `ReflectionLine`, `ReflectionPlane`, `ReflectionOrigin` |
| `create_e3.py` | 2 | `create_point()` → raise; add `create_line()`; add origin check `create_plane()`; add `create_reflection_line()`, `create_reflection_plane()`; N3-only stubs |
| `analysis_e3.py` | 2 | Fix grade→entity mapping; IPNS grade 2 → Line; split reflection detection |
| `create_p3.py` | 3 | Fix `create_line()` formula; add `create_reflection_line()`, `create_reflection_plane()`, `create_reflection_origin()`; add IPNS plane; N3-only stubs |
| `analysis_p3.py` | 3 | Fix `_line_from_factors()`; split reflection detection for 3 types |
| `create_n3.py` | 4 | Direct IPNS sphere/plane; fix reflection_plane (distance); fix inversion; fix dilator sign; fix circle; NotImplementedError stubs |
| `analysis_n3.py` | 4 | Perwass analysis formulas; fix translator/dilator extraction; fix operator classification |
| `entities.py` | 5 | Add `ImagSphere`, `ImagPointPair`, `ImagCircle` dataclasses |
| `operators.py` | 5 | Add `Reflector` dataclass; fix `GeneralDilator` translator field |
| `create_n3.py` | 5 | Add `create_imag_sphere`, `create_imag_point_pair`, `create_imag_circle`, `create_general_rotor`, `create_general_dilator`; fix `create_circle`; add `create_motor` convenience |
| `create_e3.py` / `create_p3.py` | 5 | Add `create_reflector` (cross-space utility) |
| `analysis_n3.py` | 5 | Add imag sphere/point pair/circle, general rotor, general dilator detection |
| `create.py` | 2-5 | Routing for new/renamed functions and exception stubs |
| `analysis.py` | — | No changes (dispatcher only) |
