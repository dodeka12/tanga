# Phase 4b — Visualizer API Cleanup

**Prerequisites:** Phases 1–4a implemented (Python server + frontend functional, geo_fix synced)

**Goal:** Clean up the `Visualizer` API: add a default `opns` flag, replace
`Any` with explicit input types, remove the redundant `kind` parameter,
and replace `**kwargs` rendering properties with a typed `ObjVizProps` dataclass.

---

## 1. `opns` Default on Visualizer

### 1.1 Current State

Every method that accepts an `opns` parameter has `opns: bool = True` hardcoded:

```python
def add(self, obj, *, opns: bool = True, ...):
def update_entity(self, entity_id, obj, *, opns: bool = True):
def _resolve(self, obj, *, opns: bool = True):
```

### 1.2 Proposed Change

Add `opns: bool = True` to the `Visualizer.__init__` constructor and store as `self._opns`.
All methods that accept `opns` change their default to `None`, resolving to `self._opns`
at runtime:

```python
class Visualizer:
    def __init__(self, *, opns: bool = True, ...):
        self._opns = opns
        ...

    def add(self, obj, *, opns: bool | None = None, props=None):
        if opns is None:
            opns = self._opns
        entity = self._resolve(obj, opns=opns)
        ...

    def update_entity(self, entity_id, obj, *, opns: bool | None = None):
        if opns is None:
            opns = self._opns
        entity = self._resolve(obj, opns=opns)
        ...

    def _resolve(self, obj, *, opns: bool = True):
        # unchanged — always receives an explicit value from callers
```

### 1.3 Usage

```python
# All these use the instance default (opns=True):
viz = Visualizer(opns=False)       # default IPNS
viz.add(pga.point(5, 0, 0))        # analyzed as IPNS
viz.add(pga.point(5, 0, 0))        # analyzed as IPNS

# Override per-call:
viz.add(pga.point(5, 0, 0), opns=True)   # this one as OPNS
```

---

## 2. Replace `Any` in `add()` with Explicit Input Types

### 2.1 Current State

```python
def add(
    self,
    obj: GeoEntity | Any = None,
    *,
    ...
) -> str | list[str]:
```

`_resolve()` already distinguishes:
- `GeoEntity` → pass through
- `GeoOperator` (from `pytanga.geometry.operators`) → pass through
- Anything else → try `pytanga.geometry.analyze(obj)` (expects an MV)

### 2.2 Proposed Change

Create a type alias `VizInputType` that explicitly lists all acceptable input types:

```python
# In a new file py/pytanga/viz/_types.py, or at the top of visualizer.py

from __future__ import annotations

from typing import TypeAlias, Union

from pytanga.geometry.entities import Entity as GeoEntity
from pytanga.geometry.operators import Operator as GeoOperator

# Any type that can be passed to Visualizer.add()
VizInputType: TypeAlias = Union[GeoEntity, GeoOperator, "MV"]
```

The `"MV"` forward reference avoids importing `pytanga.algebra._mv` (circular import
risk — `pytanga.algebra` may import `pytanga.viz` in the future).  At runtime the
`_resolve` method does not use `isinstance(..., MV)` — it falls through to
`analyze(obj)` for unrecognised types, so the forward reference is purely for
type-checking and documentation.

The method signature becomes:

```python
def add(
    self,
    obj: VizInputType | None = None,
    *,
    ...
) -> str | list[str]:
```

If `obj is None`, a `ValueError` is raised ("Cannot add None to the scene").

### 2.3 Discussion — Is a `TypeAlias` the Best Option?

| Option | Pros | Cons |
|--------|------|------|
| **`TypeAlias`** (chosen) | Explicit, single import, easy to extend | Forward ref for MV, runtime not enforced |
| Protocol class | Structural subtyping | Overkill — we don't need duck-typing for viz input |
| `object` | Flexible | Defeats the purpose of type safety |
| Keep `Any` | No changes needed | No IDE help, no documentation |

The `TypeAlias` is the best balance: it documents exactly what the viz submodule
accepts while keeping the runtime behaviour unchanged.

---

## 3. Remove `kind` Parameter from `add()`

### 3.1 Current State

```python
def add(
    self,
    obj: GeoEntity | Any = None,
    *,
    kind: str | None = None,     # ← removable
    entity_id: str | None = None,
    opns: bool = True,
    **properties: Any,            # ← also being removed (see §4)
) -> str | list[str]:
```

The `kind` parameter is forwarded to `Scene.add()`:

```python
return self._scene.add(entity, kind=kind, entity_id=entity_id, **properties)
```

`Scene.add()` already auto-detects the kind:

```python
resolved_kind = kind or (self._kind_from_entity(entity) if entity else "Unknown")
```

Since `_resolve()` always returns an `Entity` or `Operator` (never `None` after Phase 4a),
the `kind` parameter is **never needed**.  It was originally designed for MV-backed
entities where `entity=None`, but MVs are now resolved to entities before reaching
`Scene.add()`.

### 3.2 Proposed Change

Remove the `kind` parameter from `add()` entirely.  `Scene.add()` keeps its internal
`kind` parameter (it may still receive `None` from internal callers), but the public
API no longer exposes it.

```python
def add(
    self,
    obj: VizInputType | None = None,
    *,
    entity_id: str | None = None,
    opns: bool | None = None,
    props: ObjVizProps | None = None,
) -> str | list[str]:
```

---

## 4. Replace `**properties` with `ObjVizProps` Dataclass

### 4.1 Current State

Rendering properties are passed as `**kwargs`:

```python
viz.add(Point(1, 2, 3), color="#ff4444", opacity=0.5, size=0.12, label="P₁")
```

This is flexible but has drawbacks:
- **No IDE autocompletion** — users must consult docs to know available keys
- **No type checking** — `color=123` is silently accepted and only fails at serialization
- **No documentation** — parameter list doesn't describe what each value does
- **Fragile forwarding** — `**properties` is forwarded through `add()` → `Scene.add()` → `serialize_entity()` with no validation

### 4.2 Proposed Dataclass

```python
# py/pytanga/viz/_props.py

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ObjVizProps:
    """Visual rendering properties for an entity or operator.

    All fields default to ``None``, meaning "use the Visualizer's global
    default for this property".  Setting a field to an explicit value
    overrides the global default only for that entity.

    Entity-specific properties (``size``, ``thickness``, etc.) are
    ignored when the entity kind doesn't use them.
    """

    # ── General appearance ──
    color: str | tuple[float, float, float] | tuple[float, float, float, float] | None = None
    opacity: float | None = None

    # ── Point / direction ──
    size: float | None = None          # point radius
    length: float | None = None        # direction/lines: rendered length
    thickness: float | None = None     # line cylinder radius

    # ── Infinite objects ──
    extent: float | None = None        # plane / space: half-extent of rendered quad/box

    # ── Wireframe ──
    wireframe: bool | None = None      # sphere: show wireframe overlay

    # ── Circle ──
    tube_radius: float | None = None   # circle torus tube thickness

    # ── Point pair ──
    point_size: float | None = None    # point pair: individual point radius
    line_thickness: float | None = None  # point pair: connector line thickness

    # ── Rotor ──
    disc_radius: float | None = None   # rotor disc radius

    # ── Dilator ──
    ring_count: int | None = None      # dilator: number of rings
    max_radius: float | None = None    # dilator: maximum ring radius

    # ── Labels ──
    label: str | None = None           # text annotation; None = no label
    label_offset_y: float | None = None
    label_font_size: float | None = None
    label_color: str | None = None
    label_background: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a dict of all non-None fields, suitable for the serializer."""
        result: dict[str, Any] = {}
        for fld in fields(self):
            val = getattr(self, fld.name)
            if val is not None:
                # Normalize color to hex if needed
                if fld.name == "color" and isinstance(val, tuple):
                    result[fld.name] = _normalize_color(val)
                else:
                    result[fld.name] = val
        return result
```

### 4.3 Usage

```python
from pytanga.viz import ObjVizProps

viz.add(Point(1, 2, 3), ObjVizProps(color="#ff4444", size=0.12, label="P₁"))

# Or with keyword construction (dataclass supports **)
viz.add(Point(1, 2, 3), ObjVizProps(color=(1.0, 0.0, 0.0), opacity=0.5))

# Or with no props — uses all defaults
viz.add(Point(1, 2, 3))
```

The `add()` method takes exactly one `ObjVizProps` argument (or `None`). There is **no**
`**properties` fallback — the migration is a clean break from kwargs to the dataclass.

`@dataclass` with ``frozen=True`` provides:
- Full IDE autocompletion (fields appear in suggestions)
- Type checking (mypy/pylance catch `color=123`)
- Self-documenting (each field has a docstring)
- Simple `to_dict()` for serializer integration
- Callers can use `ObjVizProps(color="red", opacity=0.5)` or `ObjVizProps()` for all-defaults

### 4.5 `add()` Signature

The `add()` method takes `props: ObjVizProps | None = None` as its rendering properties
argument.  No `**kwargs` fallback is provided — all existing callers must be updated.

```python
def add(
    self,
    obj: VizInputType | None = None,
    *,
    entity_id: str | None = None,
    opns: bool | None = None,
    props: ObjVizProps | None = None,
) -> str | list[str]:
    if props is None:
        props = ObjVizProps()
    merged = props.to_dict()
    ...
```

### 4.6 Color Normalization in `ObjVizProps`

Move `_normalize_color` out of `Visualizer` and into `ObjVizProps.to_dict()` (or a
module-level helper in `_props.py`). This keeps color handling self-contained in
the props dataclass rather than requiring the `Visualizer` to pre-process kwargs.

---

## 5. Files to Modify

| File | Changes |
|------|---------|
| `py/pytanga/viz/_types.py` | **NEW** — `VizInputType` type alias |
| `py/pytanga/viz/_props.py` | **NEW** — `ObjVizProps` dataclass with `to_dict()` |
| `py/pytanga/viz/visualizer.py` | Add `opns` to `__init__`; change `opns` defaults to `None` on `add`/`update_entity`; use `VizInputType`; remove `kind` param; accept `ObjVizProps` (no `**properties`) |
| `py/pytanga/viz/__init__.py` | Export `ObjVizProps`, `VizInputType` |

### Files NOT Modified (no downstream impact)

- `py/pytanga/viz/scene.py` — `Scene.add()` keeps its internal `kind` parameter
- `py/pytanga/viz/serializer.py` — receives a plain `dict[str, Any]` from `props.to_dict()`, unchanged
- `py/pytanga/viz/server.py` — unchanged

---

## 6. Implementation Checklist

### 6.1 `_types.py` (new file)

- [ ] **T1:** Create `py/pytanga/viz/_types.py`
- [ ] **T2:** Define `VizInputType: TypeAlias = Union[GeoEntity, GeoOperator, "MV"]` with forward reference
- [ ] **T3:** Add module docstring

### 6.2 `_props.py` (new file)

- [ ] **P1:** Create `py/pytanga/viz/_props.py`
- [ ] **P2:** Define `ObjVizProps` dataclass with all 19 fields, all defaulting to `None`
- [ ] **P3:** Each field has a docstring
- [ ] **P4:** Implement `to_dict()` — iterates `dataclasses.fields()`, skips `None`, normalises `color` tuples
- [ ] **P5:** Add `_normalize_color()` helper (moved from `visualizer.py`)
- [ ] **P6:** Consider `frozen=True` for immutability

### 6.3 `visualizer.py`

- [ ] **V1:** Add `opns: bool = True` to `__init__`, store as `self._opns`
- [ ] **V2:** Change `add(obj, *, opns)` default to `opns: bool | None = None`, resolve `self._opns` if `None`
- [ ] **V3:** Change `update_entity(entity_id, obj, *, opns)` default to `opns: bool | None = None`
- [ ] **V4:** Remove `_normalize_color` (moved to `_props.py`; keep as pass-through wrapper if needed)
- [ ] **V5:** Replace `obj: GeoEntity | Any = None` with `obj: VizInputType | None = None`
- [ ] **V6:** Remove `kind: str | None = None` parameter from `add()`
- [ ] **V7:** Add `props: ObjVizProps | None = None` parameter to `add()` (no deprecated `**properties`)
- [ ] **V8:** Convert `props.to_dict()` to dict and forward to `Scene.add()` → `**properties`
- [ ] **V9:** Update `add()` docstring

### 6.4 `__init__.py`

- [ ] **I1:** Export `ObjVizProps` and `VizInputType` in `__all__`
- [ ] **I2:** Add imports

### 6.5 Tests

- [ ] **T1:** Test `Visualizer(opns=False)` → `add(pga.point(5,0,0))` uses IPNS by default
- [ ] **T2:** Test `add(pga.point(5,0,0), opns=True)` overrides instance default
- [ ] **T3:** Test `ObjVizProps(color="red", size=0.15).to_dict()` produces correct dict
- [ ] **T4:** Test `ObjVizProps().to_dict()` returns `{}` (all None)
- [ ] **T5:** Test `ObjVizProps(color=(1.0, 0.0, 0.0)).to_dict()` normalizes to `{"color": "#ff0000"}`
- [ ] **T6:** Test `add(Point(0,0,0), ObjVizProps(color="#fff"))` works
- [ ] **T7:** Test `VizInputType` type alias is importable
- [ ] **T8:** Verify `kind` parameter removed — existing callers don't break (none pass it)
- [ ] **T9:** All 91 existing tests still pass after updating `**kwargs` → `ObjVizProps`

### 6.6 Smoke Test

- [ ] **S1:** `dev/src/test_viz_smoke.py` updated to use `ObjVizProps` and passes all 8 tests
- [ ] **S2:** `dev/src/test_viz_play.py` updated to use `ObjVizProps` and runs

---

## 7. Verification Checklist

- [ ] `Visualizer(opns=False)` stores the default and all entity additions use IPNS
- [ ] Per-call `opns=True` overrides the instance default
- [ ] `VizInputType` type alias covers `GeoEntity`, `GeoOperator`, and `MV`
- [ ] `kind` parameter no longer exists on `add()`
- [ ] `ObjVizProps` dataclass provides IDE autocompletion for all 19 fields
- [ ] `ObjVizProps.to_dict()` correctly filters `None` and normalizes tuples
- [ ] `viz.add(Point(...), ObjVizProps(color="#fff"))` works
- [ ] `viz.add(Point(...), ObjVizProps())` works (all defaults)
- [ ] `viz.add(Point(...))` works (props=None → all defaults)
- [ ] No circular imports introduced
- [ ] All existing tests pass (91 backend tests)