# Phase 4 — Dispatcher Updates

Wire the 2D algebra modules into the existing dispatcher infrastructure. Three
files need modification; no new files.

## Files to Modify

### `py/pytanga/geometry/analysis.py`

The `_detect()` function must recognize 2D basis classes and the `analyze_entity()`
and `analyze_operator()` functions must dispatch to the 2D modules.

**`_detect()` changes:**
```python
def _detect(alg: Algebra) -> str:
    from pytanga.basis.e2 import BasisE2
    from pytanga.basis.n2 import BasisN2
    from pytanga.basis.p2 import BasisP2
    from pytanga.basis.pga2 import BasisPGA2
    from pytanga.basis.pga3 import BasisPGA3
    from pytanga.basis.n3 import BasisN3
    from pytanga.basis.p3 import BasisP3
    from pytanga.basis.e3 import BasisE3

    if isinstance(alg, BasisPGA3):
        return "pga3"
    elif isinstance(alg, BasisN3):
        return "n3"
    elif isinstance(alg, BasisP3):
        return "p3"
    elif isinstance(alg, BasisE3):
        return "e3"
    elif isinstance(alg, BasisPGA2):
        return "pga2"
    elif isinstance(alg, BasisN2):
        return "n2"
    elif isinstance(alg, BasisP2):
        return "p2"
    elif isinstance(alg, BasisE2):
        return "e2"
    else:
        raise ValueError(...)
```

> ⚠ **Order matters:** `BasisPGA3` before `BasisN3` (inheritance), `BasisPGA2`
> before `BasisN2` (inheritance). Base classes after all their subclasses.

**`analyze_entity()` / `analyze_operator()` changes:** Add `elif` branches for
`"e2"`, `"p2"`, `"n2"`, `"pga2"` dispatching to the new modules.

**Imports to add:**
```python
from . import analysis_e2, analysis_n2, analysis_p2, analysis_pga2
```

### `py/pytanga/geometry/create.py`

**`_detect()` changes:** Same pattern as `analysis.py` — add 2D basis classes
in correct inheritance order (PGA2 before N2).

**`create_entity()` / `create_operator()` changes:** Add 2D modules to the
`modules` dict and they'll be dispatched to automatically since all
entity/operator creation function names are the same across algebras.

**Imports to add:**
```python
from . import create_e2, create_n2, create_p2, create_pga2
```

### `py/pytanga/basis/__init__.py`

(Already done in Phase 1, listed here for completeness of the dispatcher phase.)

- Imports: `BasisE2`, `BasisP2`, `BasisN2`, `BasisPGA2`
- `_CLASS_MAP` entries: `"E2"`, `"P2"`, `"N2"`, `"PGA2"`
- `__all__` exports

### `py/pytanga/algebra/_algebra.py`

(Already done in Phase 1, listed here for completeness.)

- `_BASIS_CLASS_NAMES` must include `"E2"`, `"P2"`, `"N2"` (PGA2 is in `_NAMED_ALGEBRAS` already)

## Implementation Checklist

- [ ] 4.1  Update `py/pytanga/geometry/analysis.py` — `_detect()` for 2D bases, imports, dispatch branches
- [ ] 4.2  Update `py/pytanga/geometry/create.py` — `_detect()` for 2D bases, imports
- [ ] 4.3  Verify: `Geometry(Algebra.from_name("E2")).which_entity(mv)` dispatches to `analysis_e2`
- [ ] 4.4  Verify: `Geometry(Algebra.from_name("N2")).create(Point(1,2,0))` dispatches to `create_n2`
- [ ] 4.5  Verify: `pytanga.geometry.analyze(mv, opns=True)` works for all 4 new algebras
- [ ] 4.6  Verify: `pytanga.geometry.create.create_entity(basis, entity)` works for all 4 new algebras
- [ ] 4.7  Verify: `pytanga.geometry.create.create_operator(basis, operator)` works for all 4 new algebras
- [ ] 4.8  Verify: `Algebra.from_name("PGA2")` is detected as `"pga2"` not `"n2"` (PGA2 is a subclass of N2)
- [ ] 4.9  Verify: `viz.add(pga2_basis.point(3, 4, 0))` resolves through geometry.analyze → serializes correctly