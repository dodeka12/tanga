# Phase 3: Analysis Dispatcher and Algebra Detection

**Files:**
- `py/pytanga/geometry/analysis.py` — top-level dispatcher
- `py/pytanga/geometry/__init__.py` — updated public API (add analysis exports)

**Goal:** Implement the analysis entry point that determines the algebra type of a
multivector and delegates to algebra-specific analysis modules. Also update the
`__init__.py` to export the analysis functions.

---

## 1. Algebra Detection

### 1.1 Background

`BasisN3` and `BasisPGA3` share the **same** C++ basis (`CBasisN3`, dim=5, sig=0b10000)
but represent **different geometric models**:

| | N3 (Full Conformal) | PGA3 (Projective Sub-algebra) |
|---|---|---|
| Null vectors | `einf = ep + em` and `eo = 0.5·em - 0.5·ep` | `einf = ep + em` only |
| Entities | Point, PointPair, Line, Circle, Plane, Sphere, Space | Point, Direction, Line, Plane, Space |
| Operators | Reflection, Inversion, Rotor, Translator, Dilator, GeneralDilator, Motor, GeneralRotor | Reflection, Rotor, Translator, Motor |

### 1.2 Detection Strategy

Since `BasisPGA3` is a **subclass** of `BasisN3`, we must check `BasisPGA3` **first**:

| Algebra | dim | sig | Python Class | Dispatch Key |
|---------|-----|-----|-------------|-------------|
| E3 | 3 | 0 | `BasisE3` | `"e3"` |
| P3 | 4 | 0 | `BasisP3` | `"p3"` |
| N3 (CGA) | 5 | 0b10000 | `BasisN3` (not PGA3) | `"n3"` |
| PGA3 | 5 | 0b10000 | `BasisPGA3` | `"pga3"` |

**Do NOT use signature-based detection** for N3 vs PGA3 — only `isinstance()` can distinguish them.

---

## 2. `analysis.py` Implementation

```python
# py/pytanga/geometry/analysis.py

"""Top-level analysis dispatcher for geometric entities and operators.

Determines the algebra type of a multivector and delegates to the
appropriate algebra-specific analysis module.
"""

from __future__ import annotations

from pytanga.algebra._algebra import Algebra
from pytanga.algebra._mv import MV
from pytanga.basis.e3 import BasisE3
from pytanga.basis.p3 import BasisP3
from pytanga.basis.n3 import BasisN3
from pytanga.basis.pga3 import BasisPGA3

from .entities import Entity
from .operators import Operator

# Algebra-specific analysis modules (imported lazily or eagerly)
from . import analysis_e3, analysis_p3, analysis_pga3, analysis_n3


def _detect(alg: Algebra) -> str:
    """Return 'e3', 'p3', 'pga3', or 'n3'.

    Uses isinstance checks because PGA3 (subclass) and N3 (base class)
    share the same (dim=5, sig=0b10000) signature but are different
    geometric models. PGA3 is checked first since it is a subclass of N3.
    """
    if isinstance(alg, BasisPGA3):
        return "pga3"
    elif isinstance(alg, BasisN3):
        return "n3"
    elif isinstance(alg, BasisP3):
        return "p3"
    elif isinstance(alg, BasisE3):
        return "e3"
    else:
        raise ValueError(
            f"Unknown algebra type: {type(alg).__name__} "
            f"(dim={alg.dim}, sig={bin(alg.sig)})"
        )


def analyze_entity(mv: MV) -> Entity:
    """Determine which geometric entity an MV represents.

    Args:
        mv: A multivector to analyze.

    Returns:
        An Entity dataclass (Point, Line, Plane, Circle, Sphere, etc.).

    Raises:
        ValueError: If the MV cannot be identified as a known entity type.
    """
    alg_type = _detect(mv._alg)
    if alg_type == "e3":
        return analysis_e3.analyze_entity(mv)
    elif alg_type == "p3":
        return analysis_p3.analyze_entity(mv)
    elif alg_type == "pga3":
        return analysis_pga3.analyze_entity(mv)
    elif alg_type == "n3":
        return analysis_n3.analyze_entity(mv)


def analyze_operator(mv: MV) -> Operator:
    """Determine which versor/operator an MV represents.

    Args:
        mv: A multivector to analyze.

    Returns:
        An Operator dataclass (Rotor, Translator, Motor, Reflection, etc.).

    Raises:
        ValueError: If the MV cannot be identified as a known operator type.
    """
    alg_type = _detect(mv._alg)
    if alg_type == "e3":
        return analysis_e3.analyze_operator(mv)
    elif alg_type == "p3":
        return analysis_p3.analyze_operator(mv)
    elif alg_type == "pga3":
        return analysis_pga3.analyze_operator(mv)
    elif alg_type == "n3":
        return analysis_n3.analyze_operator(mv)


def analyze(mv: MV) -> Entity | Operator:
    """Try to analyze an MV as either an entity or operator.

    Tries entity analysis first, then operator analysis.
    Returns the first successful match.

    Args:
        mv: A multivector to analyze.

    Returns:
        Either an Entity or an Operator dataclass.

    Raises:
        ValueError: If the MV cannot be identified as either
                    an entity or an operator.
    """
    try:
        return analyze_entity(mv)
    except ValueError:
        pass
    try:
        return analyze_operator(mv)
    except ValueError:
        pass
    raise ValueError(
        f"Could not identify MV as entity or operator "
        f"in algebra {type(mv._alg).__name__}"
    )
```

---

## 3. Common Analysis Pattern

Each algebra-specific analysis module must provide:

### Entity Detection
- `analyze_entity(mv: MV) → Entity` — detect and decompose entity
- `make_point(alg, x, y, z) → MV` etc. — entity construction

### Operator Detection
- `analyze_operator(mv: MV) → Operator` — detect and decompose operator
- `make_rotor(alg, angle, axis) → MV` etc. — operator construction

### Core Algorithms

Entity detection uses `blade_factorize()` (backed by C++ `FactorizeBlade()`):
- Factorizes a grade-k blade into k normalized grade-1 vectors.
- Factor vectors map to geometric primitives (points, normals, directions).

Operator detection uses `blade_factorize_versor()` (backed by C++ `FactorizeVersor()`):
- Factorizes a versor into `(scale, [reflector_factors])`.
- Each factor is a reflector (grade-1). Classification by number of factors.

---

## 4. `__init__.py` — Update

```python
# py/pytanga/geometry/__init__.py

"""Geometric entity and operator analysis for TANGA."""

from .entities import (
    Point,
    Direction,
    PointPair,
    Line,
    Plane,
    Circle,
    Sphere,
    Space,
    Entity,
)

from .operators import (
    Reflection,
    Inversion,
    Rotor,
    Translator,
    Dilator,
    Motor,
    GeneralRotor,
    GeneralDilator,
    Operator,
)

from .analysis import (
    analyze,
    analyze_entity,
    analyze_operator,
)

__all__ = [
    # Entities
    "Point",
    "Direction",
    "PointPair",
    "Line",
    "Plane",
    "Circle",
    "Sphere",
    "Space",
    "Entity",
    # Operators
    "Reflection",
    "Inversion",
    "Rotor",
    "Translator",
    "Dilator",
    "Motor",
    "GeneralRotor",
    "GeneralDilator",
    "Operator",
    # Analysis
    "analyze",
    "analyze_entity",
    "analyze_operator",
]
```

---

## 5. Implementation Steps

1. Create `py/pytanga/geometry/analysis.py` with `_detect()`, `analyze_entity()`, `analyze_operator()`, `analyze()`.
2. Create stub files for all four algebra-specific modules (imported by the dispatcher):
   - `analysis_e3.py` — raise `NotImplementedError` initially
   - `analysis_p3.py` — raise `NotImplementedError` initially
   - `analysis_pga3.py` — raise `NotImplementedError` initially
   - `analysis_n3.py` — raise `NotImplementedError` initially
3. Update `py/pytanga/geometry/__init__.py` to export analysis functions.

## 6. Verification

- [ ] `_detect()` returns correct key for E3, P3, PGA3, and N3 algebra instances
- [ ] `_detect()` correctly distinguishes PGA3 from N3 (PGA3 checked first)
- [ ] `analyze_entity()` dispatches to correct module
- [ ] `analyze_operator()` dispatches to correct module
- [ ] `analyze()` falls through entity → operator with clear error
- [ ] Stub modules raise `NotImplementedError` so tests can verify dispatch without full implementation