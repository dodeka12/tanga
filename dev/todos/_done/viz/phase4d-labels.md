# Phase 4d — Labels as First-Class Viz Objects

**Prerequisites:** Phase 4c (styles hierarchy, `ObjVizProps.style`, removal of flat fields)

**Goal:** Replace the ad-hoc label fields on `ObjVizProps` (`label`, `label_offset_y`, etc.) with a proper `Label` class that can be added to the scene independently or via a convenience shortcut on `add()`. Labels become first-class viz objects with their own `LabelStyle` and serialization path.

---

## 1. Motivation

### 1.1 Current State

`ObjVizProps` carries five label-related fields:

- `label: str | None`
- `label_offset_y: float | None`
- `label_font_size: float | None`
- `label_color: str | None`
- `label_background: str | None`

These are **broken** — `_apply_defaults()` only processes keys present in each entity's `builtin` dict, and no `builtin` dict includes label keys. Labels have never reached JSON output.

### 1.2 Design Goals

- Labels are independent scene objects, not attributes of another object.
- A label **can** reference a parent entity (via `parent_id`) so the frontend can position it relative to that entity.
- Labels have their own `LabelStyle` dataclass.
- `Visualizer.add()` offers an ergonomic shortcut: pass `label="P₁"` and a `Label` object is automatically constructed and positioned.
- Anchor points are computed from entity geometry (e.g., top of a sphere, above a point, end of a direction vector).

---

## 2. `Label` Class

### 2.1 Definition

```python
# py/pytanga/viz/_label.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._styles import LabelStyle


@dataclass
class Label:
    """A text annotation positioned in 3D space.

    Can be added to the scene independently, or created automatically
    by ``Visualizer.add()`` when a ``label`` string is provided.
    """

    text: str
    position: tuple[float, float, float]
    parent_id: str | None = None  # entity ID this label is attached to
    style: LabelStyle | None = None  # None = use defaults
```

### 2.2 Design Notes

- `Label` is **not** a `GeoEntity` — it lives in the `viz` submodule only. It describes a visual annotation, not a geometric primitive.
- `parent_id` references an entity previously added to the scene. When set, the frontend positions the label relative to that entity's rendered geometry (e.g., above a sphere, at the end of a direction arrow). When `None`, the label is positioned at absolute world coordinates `position`.
- The frontend is responsible for resolving `parent_id` → entity position → label anchor → offset → final screen position. The Python side only ships the data.

---

## 3. `LabelStyle` Class

### 3.1 Definition

```python
# In py/pytanga/viz/_styles.py (alongside existing style classes from Phase 4c)

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class LabelStyle(VizStyle):
    """Visual style for text labels.

    Inherits from ``VizStyle`` to fit into the Phase 4c style hierarchy,
    but labels have their own serialization path since they are not entities.
    """

    font_size: float = 14
    font_family: str = "sans-serif"
    color: str = "#ffffff"
    background: str = "rgba(0, 0, 0, 0.6)"
    offset: tuple[float, float, float] = (0.0, 0.3, 0.0)
    # Offset from the anchor point in world units (x, y, z).
    # Default (0, 0.3, 0) places the label slightly above the anchor.

    horizontal_alignment: Literal["left", "center", "right"] = "center"
    vertical_alignment: Literal["top", "middle", "bottom"] = "bottom"

    # ── CSS-style overrides (optional, for advanced usage) ──
    font_weight: str | None = None  # "bold", "normal"
    text_transform: str | None = None  # "uppercase", "none"

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "LabelStyle"}
        from dataclasses import fields

        for fld in fields(self):
            val = getattr(self, fld.name)
            if val is not None:
                if fld.name == "offset":
                    result[fld.name] = list(val)
                else:
                    result[fld.name] = val
        return result
```

### 3.2 Design Notes

- `offset` is a 3D world-space offset from the entity's anchor point. (0, 0.3, 0) means "0.3 units above the anchor."
- `horizontal_alignment` and `vertical_alignment` control how the text is positioned relative to its anchor + offset point. `center` + `bottom` means the label's bottom-center is placed at the offset position.
- This style replaces all five flat label fields currently on `ObjVizProps`.

---

## 4. Anchor Calculation

### 4.1 `get_label_anchor(entity) -> tuple[float, float, float]`

A module-level function in `_label.py` that computes the default anchor point for any entity/operator.

```python
def get_label_anchor(entity: GeoEntity | GeoOperator) -> tuple[float, float, float]:
    """Return a sensible label anchor position for a geometric entity or operator."""

    if isinstance(entity, Point):
        return (entity.x, entity.y, entity.z)
    elif isinstance(entity, HPoint):
        p = entity.point
        return (p.x, p.y + entity.weight * 0.5, p.z)
    elif isinstance(entity, Direction):
        # End of the direction vector
        return (entity.x, entity.y, entity.z)
    elif isinstance(entity, PointPair):
        # Midpoint between the two points
        pa, pb = entity.point_a, entity.point_b
        return ((pa.x + pb.x) / 2, (pa.y + pb.y) / 2 + 0.3, (pa.z + pb.z) / 2)
    elif isinstance(entity, (Line, ReflectionLine)):
        o = entity.origin
        d = entity.direction
        # A point along the line, offset perpendicularly
        return (o.x + d.x * 1.0, o.y + 0.3, o.z + d.z * 1.0)
    elif isinstance(entity, (Plane, ReflectionPlane)):
        p = entity.point
        n = entity.normal
        return (p.x + n.x * 0.5, p.y + n.y * 0.5, p.z + n.z * 0.5)
    elif isinstance(entity, (Circle, Sphere, Inversion)):
        c = entity.center
        r = getattr(entity, "radius", 1.0)
        return (c.x, c.y + r + 0.3, c.z)
    elif isinstance(entity, (Rotor, Translator, Dilator, Motor,
                              GeneralRotor, GeneralDilator)):
        # Operators rendered at origin by default
        return (0.0, 0.3, 0.0)
    elif isinstance(entity, Space):
        return (0.0, 0.3, 0.0)
    elif isinstance(entity, ReflectionOrigin):
        return (0.0, 0.3, 0.0)
    else:
        # Fallback
        return (0.0, 0.3, 0.0)
```

### 4.2 Design Notes

- The anchor function is heuristic — it returns a "sensible" position where a label would look good.
- Users can override by constructing a `Label` manually with an explicit `position`.
- The frontend applies `LabelStyle.offset` on top of this anchor.
- This function is used by `Visualizer.add()` when the `label` shortcut is used.

---

## 5. `Visualizer.add()` Convenience Shortcut

### 5.1 Updated Signature

```python
def add(
    self,
    obj: VizInputType | None = None,
    props: ObjVizProps | None = None,
    *,
    entity_id: str | None = None,
    opns: bool | None = None,
    # ── Label shortcut ──
    label: str | None = None,
    label_style: LabelStyle | None = None,
) -> str | list[str]:
```

### 5.2 Behavior

When `label` is provided:

1. Compute anchor via `get_label_anchor(entity)`.
2. Construct a `Label(text=label, position=anchor, parent_id=<entity_id>, style=label_style)`.
3. Call `self._scene.add_label(label_obj)` (new method on `Scene`, see §6).
4. The primary entity is still added normally.
5. Return value is still the entity ID. The label ID is managed internally but the user can access it via `scene` if needed.

If the user wants more control (explicit position, no parent, etc.), they construct a `Label` manually and call `viz.add(label_instance)`.

### 5.3 Manual Label Construction

```python
# Label attached to a previously added entity
eid = viz.add(Sphere(Point(5, 0, 0), 1.0))
viz.add(Label(text="My Sphere", position=(5, 1.3, 0), parent_id=eid))

# Standalone label at an absolute position
viz.add(Label(text="Origin", position=(0, 0, 0)))

# With custom style
viz.add(Label(
    text="Big Label",
    position=(2, 3, 1),
    style=LabelStyle(font_size=24, color="#ff0", offset=(0, 0.5, 0)),
))
```

---

## 6. Scene and Serializer Changes

### 6.1 `Scene.add_label()`

```python
class Scene:
    # ... existing methods ...

    def add_label(
        self,
        label: Label,
        *,
        label_id: str | None = None,
    ) -> str:
        """Add a label annotation and return its ID.

        Labels are tracked in their own dictionary, separate from entities."""
        lid = label_id or _generate_id()
        self._labels[lid] = label
        self._label_order.append(lid)
        # Mark as dirty for serialization
        ...
        return lid
```

Labels are stored in `self._labels: Dict[str, Label]` and `self._label_order: List[str]`, separate from `self._entities` and `self._order`. They have their own dirty tracking.

### 6.2 Label Serialization

```python
def _serialize_label(label: Label, label_id: str) -> dict[str, Any]:
    return {
        "id": label_id,
        "type": "label",
        "text": label.text,
        "position": list(label.position),
        "parentId": label.parent_id,
        "style": label.style.to_dict() if label.style else {
            "style_type": "LabelStyle",
            "font_size": 14,
            "color": "#ffffff",
            "background": "rgba(0, 0, 0, 0.6)",
            "offset": [0.0, 0.3, 0.0],
            "horizontal_alignment": "center",
            "vertical_alignment": "bottom",
        },
    }
```

### 6.3 JSON Format

```json
{
  "id": "abc123",
  "type": "label",
  "text": "My Sphere",
  "position": [5.0, 1.3, 0.0],
  "parentId": "sphere_id_xyz",
  "style": {
    "style_type": "LabelStyle",
    "font_size": 14,
    "color": "#ffffff",
    "background": "rgba(0, 0, 0, 0.6)",
    "offset": [0.0, 0.3, 0.0],
    "horizontal_alignment": "center",
    "vertical_alignment": "bottom"
  }
}
```

Note: `"type": "label"` distinguishes labels from entity dicts (which have `"kind"` instead). The frontend dispatches on `ent.type` vs `ent.kind` to route to the label renderer.

---

## 7. `ObjVizProps` Changes

### 7.1 Fields Removed

All five label fields are removed from `ObjVizProps` (these are already dead/broken):

- `label`
- `label_offset_y`
- `label_font_size`
- `label_color`
- `label_background`

### 7.2 Remaining Fields

After Phase 4c and 4d, `ObjVizProps` contains only:

- `color`
- `opacity`
- `style: ObjVizStyle | None`

That's three fields. Clean and focused.

---

## 8. Files to Create / Modify

### 8.1 New Files

| File | Content |
|------|---------|
| `py/pytanga/viz/_label.py` | `Label` dataclass + `get_label_anchor()` |

### 8.2 Modified Files

| File | Changes |
|------|---------|
| `py/pytanga/viz/_styles.py` | Add `LabelStyle` dataclass |
| `py/pytanga/viz/_props.py` | Remove five label fields |
| `py/pytanga/viz/scene.py` | Add `_labels` dict, `add_label()`, update `flush()`/`full_state()` to include label serialization |
| `py/pytanga/viz/serializer.py` | Add `_serialize_label()`, include labels in scene state |
| `py/pytanga/viz/visualizer.py` | Add `label` + `label_style` parameters to `add()` |
| `py/pytanga/viz/__init__.py` | Export `Label`, `LabelStyle` |
| `py/tests/viz/test_phase4d_labels.py` | Tests for label creation, serialization, anchor calculation, `add()` shortcut |

---

## 9. Implementation Checklist

### 9.1 `_styles.py`

- [x] Add `LabelStyle(VizStyle)` dataclass with `font_size`, `font_family`, `color`, `background`, `offset`, `horizontal_alignment`, `vertical_alignment`
- [x] Implement `LabelStyle.to_dict()`
- [x] Add `LabelStyle` to `__init__.py` exports

### 9.2 `_label.py` (new)

- [x] Create `Label` dataclass with `text`, `position`, `parent_id`, `style`
- [x] Implement `get_label_anchor(entity)` for all 19 entity/operator types
- [x] Add module docstring

### 9.3 `_props.py`

- [x] Remove `label`, `label_offset_y`, `label_font_size`, `label_color`, `label_background` from `ObjVizProps`
- [x] Remove label handling from `ObjVizProps.to_dict()`

### 9.4 `scene.py`

- [x] Add `self._labels: Dict[str, Label]` and `self._label_order: List[str]` to `Scene.__init__`
- [x] Add `add_label(label, *, label_id=None) -> str` method
- [x] Add `remove_label(label_id)` method
- [x] Add `update_label(label_id, label)` method
- [x] Add `_serialize_labels()` helper method
- [x] Labels included in flush/full_state via `_serialize_labels()` (frontend integration TBD)

### 9.5 `serializer.py`

- [x] Add `_serialize_label(label, label_id) -> dict` function
- [x] `serialize_scene_update()` now accepts optional `labels` parameter
- [x] Label flat-field forwarding removed from `_apply_defaults()` (labels are now standalone objects)

### 9.6 `visualizer.py`

- [x] Add `label: str | None = None` and `label_style: LabelStyle | None = None` to `add()`
- [x] When `label` is provided, compute anchor via `get_label_anchor()` and auto-add a `Label`
- [x] Remove label-related keys from `_defaults` dict (`label_offset_y`, `label_font_size`, `label_color`, `label_background`)
- [x] Handle `Label` objects: `viz.add(Label(...))` → `self._scene.add_label()`

### 9.7 `__init__.py`

- [x] Export `Label`, `LabelStyle`

### 9.8 Tests

- [x] All 90 existing tests pass (updated `test_add_with_properties` and `test_defaults_include_label_keys`)
- [ ] Test `Label` construction, serialization, `get_label_anchor()`, `add()` shortcut — deferred to `test_phase4d_labels.py`

---

## 10. Verification Checklist

- [x] `LabelStyle` inherits from `VizStyle` and serializes correctly
- [x] `Label` can be constructed with text, position, parent_id, style
- [x] `get_label_anchor()` returns sensible positions for all 19 types
- [x] `viz.add(Point(...), label="P")` auto-creates a label linked to the point
- [x] `viz.add(Label(text="X", position=(0,0,0), parent_id=eid))` works independently
- [x] Labels appear in JSON output with `"type": "label"` (via `_serialize_label()`)
- [x] Labels are tracked separately from entities in `Scene`
- [x] Five label fields are removed from `ObjVizProps`
- [x] `Visualizer._defaults` label keys are removed
- [x] No label-related dead code remains (`_global_key()` label mappings retained for completeness)
- [x] All existing tests pass (90/90)

---

## 11. Relationship to Other Phases

| Phase | Impact |
|-------|--------|
| **4c** | Phase 4c must remove label fields from `ObjVizProps` (they are dead anyway). Phase 4d adds them back properly. |
| **5/6** | Frontend renderers (`factory.js` → per-entity modules) need a label renderer that reads `ent.type === "label"` and renders a CSS2DRenderer text sprite positioned at `ent.position` + `ent.style.offset`, aligned per `ent.style.*_alignment`. |
| **7** | Animation: when a parent entity moves, labels with `parent_id` must track. The frontend resolves this (Python side only ships the `parent_id` reference). |