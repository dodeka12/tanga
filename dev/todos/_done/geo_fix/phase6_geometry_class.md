# Phase 6 — Geometry Convenience Class

## Scope

Add a `Geometry` class to `py/pytanga/geometry/` that wraps an algebra instance
and exposes `create()`, `which_entity()`, and `which_operator()` convenience
methods.  These delegate to the existing `create.py` and `analysis.py`
dispatchers, always using the class's stored algebra and its default `opns`
flag (overridable at call time).

## Motivation

Currently every call to `create_entity`, `create_operator`, `analyze_entity`,
or `analyze_operator` requires the caller to pass the algebra and `opns` flag
explicitly:

```python
b = Algebra.from_name("N3")
mv = create_entity(b, Point(1, 2, 3), opns=True)
result = analyze_entity(mv, opns=True)
```

A `Geometry` instance bundles the algebra and default `opns` so that common
use becomes:

```python
geo = Geometry(b, opns=True)
mv = geo.create(Point(1, 2, 3))          # uses geo.opns (True)
result = geo.which_entity(mv)            # uses geo.opns (True)
result = geo.which_entity(mv, opns=False)  # overrides
```

---

## Specification

### Class: `Geometry`

**File**: `py/pytanga/geometry/_geometry.py` (new)

```python
class Geometry:
    """High-level geometry facade bound to a single algebra.

    Parameters
    ----------
    algebra : Algebra
        The algebra instance (e.g. ``Algebra.from_name("N3")``).
        Stored immutably; access via the ``algebra`` property.
    opns : bool, optional
        Default OPNS/IPNS flag for all convenience methods.
        Can be overridden per call.  Defaults to *True*.
    """

    def __init__(self, algebra: Algebra, *, opns: bool = True) -> None:
        self._algebra = algebra
        self.opns = opns

    @property
    def algebra(self) -> Algebra:
        """The algebra this ``Geometry`` instance is bound to (read-only)."""
        return self._algebra
```

### Methods

All three methods accept an optional `opns` parameter.  When `opns` is
`None` (the default), the instance's `self.opns` is used.  Otherwise the
explicit value overrides.

| Method | Signature | Delegates to |
|--------|-----------|--------------|
| `create` | `create(obj: Entity \| Operator, *, opns: bool \| None = None) -> MV` | `create.create(basis=self.algebra, obj=obj, opns=opts_opns)` |
| `which_entity` | `which_entity(mv: MV, *, opns: bool \| None = None) -> Entity` | `analysis.analyze_entity(mv, opns=opts_opns)` |
| `which_operator` | `which_operator(mv: MV) -> Operator` | `analysis.analyze_operator(mv)` |

`which_operator` does **not** accept an `opns` argument because operators
(versors) are always interpreted the same way regardless of OPNS/IPNS.

### Re-exports

- `Geometry` is added to `py/pytanga/geometry/__init__.py`'s imports and
  `__all__`.

### Design Notes

1. **`algebra` is read-only**: The `_algebra` attribute is private and
   exposed only via a property getter.  No setter is provided, so the
   algebra cannot be changed after construction.

2. **`opns` is mutable**: The `self.opns` attribute is a plain public
   attribute — callers can change it at any time to switch the default
   behaviour for subsequent calls.

3. **No type coercion**: The methods delegate directly to the existing
   dispatchers; no additional validation is performed.

4. **Naming**: The analysis methods are named `which_entity` and
   `which_operator` to distinguish them from the free functions
   `analyze_entity` / `analyze_operator` and to read as natural-language
   queries ("which entity does this MV represent?").

---

## Files to Modify

| File | Change |
|------|--------|
| `py/pytanga/geometry/_geometry.py` | **New** — `Geometry` class |
| `py/pytanga/geometry/__init__.py` | Import and export `Geometry` |
| `dev/todos/geo_fix/overview_plan.md` | Add Phase 6 entry |

## Implementation Checklist

### `_geometry.py` (new)

- [ ] Create `Geometry` class with `__init__(self, algebra, *, opns=True)`.
- [ ] Private `_algebra` attribute; public `opns` attribute.
- [ ] `algebra` property getter (read-only).
- [ ] `create(obj, *, opns=None)` → calls `create.create(self.algebra, obj, opns=effective_opns)`.
- [ ] `which_entity(mv, *, opns=None)` → calls `analysis.analyze_entity(mv, opns=effective_opns)`.
- [ ] `which_operator(mv)` → calls `analysis.analyze_operator(mv)`.
- [ ] Helper `_opns(override)` returning `self.opns if override is None else override`.

### `__init__.py`

- [ ] Import `Geometry` from `._geometry`.
- [ ] Add `"Geometry"` to `__all__`.

### `overview_plan.md`

- [ ] Add Phase 6 description and checklist link.

### Tests

- [ ] **Test: algebra is read-only**: `geo.algebra` returns the stored algebra; attempting `geo.algebra = …` raises `AttributeError`.
- [ ] **Test: default opns**: `Geometry(b, opns=True).create(Point(1,2,3))` calls dispatcher with `opns=True`.
- [ ] **Test: default opns = False**: `Geometry(b, opns=False).create(Point(1,2,3))` calls dispatcher with `opns=False`.
- [ ] **Test: explicit opns overrides**: `geo.create(point, opns=False)` uses `False` even when `geo.opns = True`.
- [ ] **Test: opns can be changed**: `geo.opns = False` changes default for subsequent calls.
- [ ] **Test: which_entity round-trip**: `geo.which_entity(geo.create(sphere)) ≈ sphere`.
- [ ] **Test: which_operator round-trip**: `geo.which_operator(geo.create(rotor)) ≈ rotor`.
- [ ] **Test: which_operator ignores opns**: passing `opns=False` to `which_operator` has no effect (or raises `TypeError` — decide which).
- [ ] **Test: Geometry is importable from pytanga.geometry**: `from pytanga.geometry import Geometry`.