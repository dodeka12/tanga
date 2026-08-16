# Phase 2 — Typed Per-Entity Analyzers

**Prerequisites:** Phase 1 (`mv.algebra.opns` exists).

**Goal:** Add explicit public per-entity analyzer functions to every `analysis_*`
module. Each typed analyzer reads `mv.algebra.opns`, dualizes to OPNS if the
algebra is in IPNS mode, calls the existing internal decomposer, and **raises a
clear error** if the result is not the expected entity type.

---

## 1. Naming and Availability Matrix

Every typed function has signature `analyze_X(mv: MV) -> X` where `X` is the
entity class. Cells marked "–" are **not** added for that algebra (the entity is
not representable).

| Function | E2 | E3 | P2 | P3 | N2 | N3 | PGA2 | PGA3 |
|---|---|---|---|---|---|---|---|---|
| `analyze_point` | – | – | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `analyze_direction` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `analyze_line` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `analyze_plane` | – | ✓ | – | ✓ | – | ✓ | – | ✓ |
| `analyze_circle` | – | – | – | – | ✓ | ✓ | – | – |
| `analyze_sphere` | – | – | – | – | ✓ | ✓ | – | – |
| `analyze_point_pair` | – | – | – | – | ✓ | ✓ | – | – |
| `analyze_hpoint` | – | – | – | – | ✓ | ✓ | – | – |
| `analyze_hdirection` | – | – | – | – | ✓ | ✓ | – | – |
| `analyze_space` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

For E2/E3 `analyze_line`: a line is an **IPNS** entity (grade-2 bivector in E3,
grade-2 in E2 is only reached via IPNS). These analyzers therefore interpret the
input through the currently selected interpretation and must call the IPNS line
decomposer directly (not dualize to OPNS). They still respect `mv.algebra.opns`
in the sense of only succeeding when the flag/input combination actually
produces a line (`analyze_entity(mv)` returns `Line`), and raise otherwise.

---

## 2. Shared Helper Shape

For each algebra module, the typed analyzers follow one of two patterns:

### OPNS-dominant algebras (P2/P3/N2/N3):

```python
def analyze_point(mv: MV) -> Point:
    """Interpret *mv* (in the algebra's OPNS/IPNS mode) as a Point.

    Raises ``TypeError`` if the interpreted entity is not a Point.
    """
    result = analyze_entity(mv)          # already reads mv.algebra.opns
    if not isinstance(result, Point):
        raise TypeError(f"Expected a Point, got {type(result).__name__}")
    return result
```

This first approach reuses `analyze_entity`, but must be **inverted** relative to
Phase 4: until Phase 4, `analyze_entity` still accepts `opns`, so Phase 2 calls
`analyze_entity(mv, opns=mv.algebra.opns)`. After Phase 4 the argument is dropped.

### Direct-decomposer algebras (where `analyze_entity` returns `None` for
degenerate/null-space or needs grade disambiguation — notably N2/N3 and PGA):

```python
def analyze_point(mv: MV) -> Point:
    if not mv.algebra.opns:
        mv = mv.dual()
    # grade check + call the internal decomposer, e.g. _point_or_direction_n3
    ...
```

**Key rule:** never hard-code a grade that is convention-dependent. Reuse the
existing private decomposers (`_point_or_direction_*`, `_line_from_*`,
`_plane_from_*`, `_decompose_circle`, `_sphere_from_ipns`, `_point_from_trivector`,
`_point_from_bivector`, etc.).

---

## 3. Per-Algebra Mapping to Existing Decomposers

| Algebra | `analyze_point` | `analyze_direction` | `analyze_line` | `analyze_plane` | notes |
|---|---|---|---|---|---|
| e2 | – | `_direction_from_factor` / IPNS `_direction_from_ipns_vector` | `_line_from_ipns_vector` | – | |
| e3 | – | `_direction_from_factor` | `_line_from_ipns_bivector` | OPNS `_plane_from_bivector` / IPNS `_plane_from_ipns_vector` | |
| p2 | `_point_or_direction_from_coeffs` | same | `_line_from_factors` | – | point/direction share a decomposer with w==0 branch |
| p3 | `_point_or_direction_from_coeffs` | same | `_line_from_factors` | `_plane_from_trivector` | |
| n2 | `_point_or_direction_n2` | same | `_decompose_line` / `_line_from_ipns_opns` | – (2D plane is a line) | |
| n3 | `_point_or_direction_n3` | same | `_decompose_line` | `_plane_from_ipns` | |
| pga2 | `_point_from_bivector` / `_point_or_direction_from_ipns` | same | `_line_from_vector` | – | |
| pga3 | `_point_from_trivector` | same | `_line_from_bivector` | `_plane_from_vector` | |

Additional conformal analyzers (`n2`, `n3`) map to:
- `analyze_circle` → `_decompose_circle` (after resolving IPNS/OPNS + grade)
- `analyze_sphere` → `_sphere_from_ipns(mv.dual(), ...)`
- `analyze_point_pair` → `_decompose_grade2`
- `analyze_hpoint` / `analyze_hdirection` → `_decompose_grade2` branches
- `analyze_space` → grade checks + `blade_factorize_versor` / `mv.dual().is_scalar`

---

## 4. Error Contract

- Wrong structural type → `TypeError(f"Expected a {ExpectedName}, got {actual}")`.
- `None` (empty null-space) or malformed (zero/mixed-grade) → `ValueError`, as the
  underlying decomposers already raise.
- Unsupported algebra for an entity (e.g. `analyze_point` in E3) → **don't define**
  the function in that module; the shared dispatcher raises when mapping.

---

## 5. Shared Dispatcher Re-export

Add to `py/pytanga/geometry/analysis.py` (Phase 4 wires the no-arg `analyze_entity`):

```python
from .analysis_e3 import analyze_direction as analyze_direction  # (illustrative)
```

Concretely, `analysis.py` gains thin `analyze_point(mv)` / `analyze_direction(mv)`
/ … functions that call `_detect(mv._alg)` → the matching `analysis_*` module
function (mirroring `analyze_entity`'s dispatch). `Entity` constructors call these
shared dispatchers, so they never import the per-algebra modules directly.

For entities not supported by an algebra, the shared dispatcher raises
`TypeError(f"{Entity} is not supported in {alg_type}")`.

---

## 6. Tests (Phase 2)

New file `py/tests/geometry/test_typed_analyzers.py` (parametrized over the
supported algebras, each with an `opns=True` fixture and an `opns=False` fixture):

For each supported (algebra, entity):
- `analyze_X(create_entity(alg, X(...)))` returns an `X` with matching fields.

Mismatch tests:
- `analyze_point(line_mv)` raises `TypeError`.
- `analyze_space(point_mv)` raises `TypeError`.
- In E3, calling `analyze_point` via the shared dispatcher raises
  `TypeError` (unsupported).
- IPNS-mode: `alg.opns = False; analyze_point(create_entity(alg, Point(...)))` round-trips.

No existing tests change in Phase 2 (typed analyzers are additive).

---

## 7. Implementation Checklist

- [x] Add typed analyzers to `analysis_e2.py`
- [x] Add typed analyzers to `analysis_e3.py`
- [x] Add typed analyzers to `analysis_p2.py`
- [x] Add typed analyzers to `analysis_p3.py`
- [x] Add typed analyzers to `analysis_n2.py`
- [x] Add typed analyzers to `analysis_n3.py`
- [x] Add typed analyzers to `analysis_pga2.py`
- [x] Add typed analyzers to `analysis_pga3.py`
- [x] Add shared dispatchers in `analysis.py` (calling `_detect`)
- [x] Add `py/tests/geometry/test_typed_analyzers.py`
- [x] Run: `pytest py/tests/geometry/test_typed_analyzers.py -q`

---

## 8. Verification

- [x] Every matrix cell marked ✓ round-trips via `create_entity` + typed analyzer in both `opns` modes
- [x] Mismatched inputs raise `TypeError`
- [x] Unsupported algebra+entity raises `TypeError` from the shared dispatcher
