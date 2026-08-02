# Phase 8c — Label Anchor Frames & 2D Offsets

**Prerequisites:** Phase 8b (style classes with `None` defaults, merged canonical instances)

**Goal:** Redesign the label positioning system with per-entity **local anchor frames**,
a **3D offset in local coordinates**, a **2D pixel offset**, and **alignment control**.
The anchor point is computed purely from entity geometry (no baked-in offset), and
the offsets are separated into logical layers.

**Status:** ❌ Not started

---

## 1. Motivation

### 1.1 Current Problems

1. **`get_label_anchor()` hardcodes +0.3 Y offset** (e.g. `(c.x, c.y + r + 0.3, c.z)` for spheres).
   The offset is baked into the anchor, making it impossible to customize per-label or
   per-kind without changing the anchor function.

2. **`LabelStyle.offset` is a 3D vector** `(0.0, 0.3, 0.0)` but CSS2D labels are projected
   from 3D to 2D screen space. A Z offset causes perspective-dependent shifts. Users
   expect a **2D pixel offset** that behaves like CSS `translate`.

3. **`LabelStyle.offset` defaults to `(0, 0.3, 0)`** — the same 0.3 that's already baked
   into the anchor. The anchor **and** the offset both contribute vertical displacement,
   resulting in `y + r + 0.3 + 0.3` total shift (anchor + style offset). This is confusing
   and redundant.

4. **No per-entity-kind awareness of local orientation.** A point pair has a natural axis
   between its two points, a plane has a normal, a direction has a vector — but the label
   always floats "above" in world Y regardless. A label for a line along X should be
   offset perpendicular to the line, not globally up.

5. **No alignment control.** Labels are always positioned with their center at the anchor
   point. Users cannot left-align, right-align, or fine-tune label positioning relative
   to the anchor.

### 1.2 Design Goals

1. **Anchor = pure geometry.** `get_label_anchor()` returns the geometric center / top /
   position of an entity without any "extra margin."  No hardcoded `+0.3`.

2. **3D offset in the entity's local frame.** `LabelStyle.offset_local` is a 3-tuple
   applied in the entity's **local coordinate system**, scaled by the entity's
   characteristic size.  Default is `(0, 0, 0)` — no offset.

   ```python
   # For a sphere at (3, 0, 0) with radius 2:
   #   local x = world X, local y = world Y, scale = 2
   #   offset_local = (0, 0.0, 0)  →  label at sphere center = (3, 0, 0)
   #   offset_local = (0, 1.0, 0)  →  2 * 1.0 = 2 world units in local Y
   #                                  →  label at (3, 2, 0) = sphere surface
   #   offset_local = (0, 1.1, 0)  →  2 * 1.1 = 2.2 world units
   #                                  →  label at (3, 2.2, 0) = 10% above surface
   ```

3. **2D pixel offset.** `LabelStyle.offset_2d` is an `(x_px, y_px)` tuple applied
   in screen space after projection.  Default is `(0, 0)`.

4. **Alignment.** `LabelStyle.align` is an `(ax, ay)` tuple in `[0, 1]` where
   `(0.5, 0.5)` = center (default), `(0, 0)` = top-left at anchor,
   `(1, 1)` = bottom-right at anchor.  Maps to CSS `transform: translate(-ax*100%, -ay*100%)`.

5. **Local frame per entity kind.** Each entity type defines a local coordinate system
   (origin, axes, scale) so that offsets are meaningful and consistent.

---

## 2. Local Frame per Entity Kind

### 2.1 Frame Definition

For every entity/operator kind, a function returns a `LabelFrame`:

```python
@dataclass
class LabelFrame:
    """Local coordinate frame for label positioning.

    The 3D ``offset_local`` from ``LabelStyle`` is applied in this frame:
    ``world_offset = (ox * x_axis + oy * y_axis + oz * z_axis) * scale``.
    """
    origin: tuple[float, float, float]   # anchor origin in world coordinates
    x_axis: tuple[float, float, float]   # local X direction (unit)
    y_axis: tuple[float, float, float]   # local Y direction (unit)
    z_axis: tuple[float, float, float]   # local Z direction (unit)
    scale: float                         # characteristic size of the entity
```

### 2.2 Frame Computation per Kind

A helper chooses a perpendicular vector for a given direction: pick the world axis
with the smallest absolute dot product to the given direction, then cross.

```python
def _perpendicular(direction: tuple[float, float, float]) -> tuple[float, float, float]:
    """Return a unit vector perpendicular to *direction*.
    
    Chooses the world axis (X, Y, or Z) that is most perpendicular to
    *direction*, then returns the normalized cross product.
    """
    dx, dy, dz = direction
    # Dot products with world axes
    dots = (abs(dx), abs(dy), abs(dz))
    # Pick the axis with smallest dot → most perpendicular
    if dots[0] <= dots[1] and dots[0] <= dots[2]:
        ref = (1.0, 0.0, 0.0)
    elif dots[1] <= dots[2]:
        ref = (0.0, 1.0, 0.0)
    else:
        ref = (0.0, 0.0, 1.0)
    # Cross direction × ref → perpendicular to direction
    y = _cross(direction, ref)
    return _normalize(y)
```

#### Table: Local Frame per Entity Kind

| Entity Kind | `origin` | `x_axis` | `y_axis` | `z_axis` | `scale` |
|---|---|---|---|---|---|
| **Point** | `(x, y, z)` | `(1,0,0)` | `(0,1,0)` | `(0,0,1)` | 1.0 |
| **HPoint** | `(point.x, point.y, point.z)` | `(1,0,0)` | `(0,1,0)` | `(0,0,1)` | `weight` |
| **Direction** | `(0,0,0)` or origin if given | direction vector (normalized) | `_perpendicular(x_axis)` | `x × y` | `length` (default 2.0) |
| **PointPair** | midpoint of `point_a`, `point_b` | unit vector from `point_a` to `point_b` | `_perpendicular(x_axis)` | `x × y` | distance between points ÷ 2 |
| **Line** | origin | direction | `_perpendicular(x_axis)` | `x × y` | `length` (default 20.0) |
| **Plane** | point on plane | in-plane perpendicular to normal | in-plane perpendicular to x & normal | normal | `extent` (default 10.0) |
| **Circle** | center | in-plane (perp. to normal) | in-plane (perp. to x & normal) | normal | `radius` |
| **Sphere** | center | `(1,0,0)` | `(0,1,0)` | `(0,0,1)` | `radius` |
| **Space** | `(0,0,0)` | `(1,0,0)` | `(0,1,0)` | `(0,0,1)` | `scale` property |
| **ReflectionLine** | `(0,0,0)` | direction | `_perpendicular(x_axis)` | `x × y` | `length` (default 5.0) |
| **ReflectionPlane** | `(0,0,0)` | in-plane perpendicular to normal | in-plane | normal | `extent` (default 5.0) |
| **ReflectionOrigin** | `(0,0,0)` | `(1,0,0)` | `(0,1,0)` | `(0,0,1)` | `extent` (default 1.0) |
| **Inversion** | center | `(1,0,0)` | `(0,1,0)` | `(0,0,1)` | `radius` |
| **Rotor** | `(0,0,0)` | in-plane (perp. to rotation axis) | in-plane | rotation axis | `disc_radius` (default 1.5) |
| **Translator** | `(0,0,0)` | translation vector | `_perpendicular(x_axis)` | `x × y` | `length` (default 3.0) |
| **Dilator** | `(0,0,0)` | `(1,0,0)` | `(0,1,0)` | `(0,0,1)` | `max_radius` (default 3.0) |
| **Motor** | `(0,0,0)` | in-plane (perp. to rotation axis) | in-plane | rotation axis | 1.5 (disc radius) |
| **GeneralRotor** | `(0,0,0)` | in-plane (perp. to rotation axis) | in-plane | rotation axis | 1.5 |
| **GeneralDilator** | `(0,0,0)` | translation vector | `_perpendicular(x_axis)` | `x × y` | `max_radius` (default 3.0) |

For planes and circles, `x_axis` = a unit vector perpendicular to the normal (using `_perpendicular(normal)`), and `y_axis` = `normal × x_axis`.

---

## 3. `LabelStyle` Changes

### 3.1 Updated Fields

```python
@dataclass
class LabelStyle(VizStyle):
    """Visual style for text labels."""

    font_size: float = 14
    font_family: str = "sans-serif"
    color: str = "#ffffff"
    background: str = "rgba(0, 0, 0, 0.6)"
    font_weight: str | None = None
    text_transform: str | None = None

    # ── 3D offset in entity's local frame (scaled by entity scale) ──
    offset_local: tuple[float, float, float] | None = None
    # Default: (0, 0, 0) — no offset, label sits exactly at anchor

    # ── 2D screen-space pixel offset (after 3D → 2D projection) ──
    offset_2d: tuple[float, float] | None = None
    # Default: (0, 0) — no pixel shift

    # ── Alignment of label text relative to anchor ──
    align: tuple[float, float] | None = None
    # (0.5, 0.5) = centered on anchor (default)
    # (0, 0) = top-left corner at anchor
    # (1, 1) = bottom-right corner at anchor
```

### 3.2 Serialization

```python
def to_dict(self) -> dict[str, Any]:
    result: dict[str, Any] = {"style_type": "LabelStyle"}
    result["font_size"] = self.font_size
    result["font_family"] = self.font_family
    result["color"] = self.color
    result["background"] = self.background
    if self.font_weight is not None:
        result["font_weight"] = self.font_weight
    if self.text_transform is not None:
        result["text_transform"] = self.text_transform
    if self.offset_local is not None:
        result["offset_local"] = list(self.offset_local)
    if self.offset_2d is not None:
        result["offset_2d"] = list(self.offset_2d)
    if self.align is not None:
        result["align"] = list(self.align)
    return result
```

### 3.3 Canonical Default

```python
# In _DEFAULT_STYLE_FOR_KIND — LabelStyle is not there (labels aren't entity kinds).
# The canonical default for LabelStyle is:
_CanonicalLabelStyle = LabelStyle(
    offset_local=(0.0, 0.0, 0.0),
    offset_2d=(0.0, 0.0),
    align=(0.5, 0.5),
)
```

---

## 4. Anchor Calculation (No Hardcoded Offset)

### 4.1 Revised `get_label_anchor()`

Returns the **geometric center/top** of the entity without any margin:

```python
def get_label_anchor(entity: EntityLike) -> tuple[float, float, float]:
    """Return the natural anchor position for a label — no margin added."""

    if isinstance(entity, Point):
        return (entity.x, entity.y, entity.z)

    if isinstance(entity, HPoint):
        p = entity.point
        return (p.x, p.y, p.z)

    if isinstance(entity, Direction):
        return (0.0, 0.0, 0.0)

    if isinstance(entity, PointPair):
        pa, pb = entity.point_a, entity.point_b
        return ((pa.x + pb.x) / 2, (pa.y + pb.y) / 2, (pa.z + pb.z) / 2)

    if isinstance(entity, (Line, ReflectionLine)):
        return (entity.origin.x, entity.origin.y, entity.origin.z)

    if isinstance(entity, (Plane, ReflectionPlane)):
        return (entity.point.x, entity.point.y, entity.point.z)

    if isinstance(entity, (Circle, Sphere, Inversion)):
        return (entity.center.x, entity.center.y, entity.center.z)

    if isinstance(entity, Space):
        return (0.0, 0.0, 0.0)

    # Operators — all rendered at origin
    return (0.0, 0.0, 0.0)
```

No more `+ r + 0.3` baked in. The `offset_local` from `LabelStyle` takes care of
positioning the label above/alongside the entity.

---

## 5. `get_label_frame()` — Local Frame per Kind

```python
def get_label_frame(entity: EntityLike) -> LabelFrame:
    """Return the local coordinate frame for label positioning on *entity*."""

    origin = get_label_anchor(entity)

    # ── Entities with no intrinsic orientation ──
    if isinstance(entity, (Point, HPoint)):
        return LabelFrame(origin, (1,0,0), (0,1,0), (0,0,1), 1.0)

    if isinstance(entity, Space):
        return LabelFrame(origin, (1,0,0), (0,1,0), (0,0,1), entity.scale)

    if isinstance(entity, (Sphere, Inversion)):
        r = getattr(entity, "radius", 1.0)
        return LabelFrame(origin, (1,0,0), (0,1,0), (0,0,1), r)

    # ── Direction / Line-based ──
    if isinstance(entity, (Direction, Translator)):
        d = (entity.x, entity.y, entity.z) if isinstance(entity, Direction) else (
            entity.vector.x, entity.vector.y, entity.vector.z)
        ln = 2.0 if isinstance(entity, Direction) else (entity.length if hasattr(entity, 'length') else 3.0)
        x = _normalize(d)
        y = _perpendicular(x)
        z = _cross(x, y)
        return LabelFrame(origin, x, y, z, ln)

    if isinstance(entity, (Line, ReflectionLine)):
        d = (entity.direction.x, entity.direction.y, entity.direction.z)
        ln = 20.0 if isinstance(entity, Line) else 5.0
        x = _normalize(d)
        y = _perpendicular(x)
        z = _cross(x, y)
        return LabelFrame(origin, x, y, z, ln)

    # ── PointPair ──
    if isinstance(entity, PointPair):
        pa, pb = entity.point_a, entity.point_b
        x = _normalize((pb.x - pa.x, pb.y - pa.y, pb.z - pa.z))
        dist = _length((pb.x - pa.x, pb.y - pa.y, pb.z - pa.z))
        y = _perpendicular(x)
        z = _cross(x, y)
        return LabelFrame(origin, x, y, z, dist / 2)

    # ── Plane / ReflectionPlane ──
    if isinstance(entity, (Plane, ReflectionPlane)):
        n = (entity.normal.x, entity.normal.y, entity.normal.z)
        z = _normalize(n)
        x = _perpendicular(z)
        y = _cross(z, x)
        ext = 10.0 if isinstance(entity, Plane) else 5.0
        return LabelFrame(origin, x, y, z, ext)

    # ── Circle ──
    if isinstance(entity, Circle):
        n = (entity.normal.x, entity.normal.y, entity.normal.z)
        z = _normalize(n)
        x = _perpendicular(z)
        y = _cross(z, x)
        return LabelFrame(origin, x, y, z, entity.radius)

    # ── Rotor / Motor / GeneralRotor ──
    if isinstance(entity, (Rotor, Motor, GeneralRotor)):
        ax = entity.axis if isinstance(entity, Rotor) else (
            entity.rotor.axis if hasattr(entity, 'rotor') else Direction(0,0,1))
        z = _normalize((ax.x, ax.y, ax.z))
        x = _perpendicular(z)
        y = _cross(z, x)
        return LabelFrame(origin, x, y, z, 1.5)

    # ── Dilator / GeneralDilator ──
    if isinstance(entity, (Dilator, GeneralDilator)):
        mr = 3.0
        return LabelFrame(origin, (1,0,0), (0,1,0), (0,0,1), mr)

    if isinstance(entity, ReflectionOrigin):
        return LabelFrame(origin, (1,0,0), (0,1,0), (0,0,1), 1.0)

    # Fallback
    return LabelFrame(origin, (1,0,0), (0,1,0), (0,0,1), 1.0)
```

---

## 6. Final Anchor Computation

Given an entity `e` and a `LabelStyle style`, the final world-space anchor is:

```python
def compute_label_anchor(entity, style: LabelStyle) -> tuple[float, float, float]:
    frame = get_label_frame(entity)
    ox, oy, oz = style.offset_local or (0.0, 0.0, 0.0)
    # Apply offset in local frame, scaled:
    wx = frame.origin[0] + (ox * frame.x_axis[0] + oy * frame.y_axis[0] + oz * frame.z_axis[0]) * frame.scale
    wy = frame.origin[1] + (ox * frame.x_axis[1] + oy * frame.y_axis[1] + oz * frame.z_axis[1]) * frame.scale
    wz = frame.origin[2] + (ox * frame.x_axis[2] + oy * frame.y_axis[2] + oz * frame.z_axis[2]) * frame.scale
    return (wx, wy, wz)
```

For a sphere at `(3, 0, 0)` with `radius=2` and `offset_local=(0, 1.0, 0)`:
- `frame.origin = (3, 0, 0)`, `frame.scale = 2`
- Local Y is world Y = `(0, 1, 0)`
- `wy = 0 + 1.0 * 1.0 * 2 = 2`
- Final anchor = `(3, 2, 0)` — exactly at the sphere's top surface.

To position the label **above** the sphere with a small gap, the user would use:
`offset_local=(0, 1.1, 0)` (sphere radius + 10% gap in local space, scaled by radius)
or a 2D pixel offset after projection.

---

## 7. `Label` Stores the Computed Anchor

In `visualizer.py`'s `add()` method, when `label="S1"` is provided:

```python
if label is not None:
    lbl_style = label_style or LabelStyle()
    anchor = compute_label_anchor(entity, lbl_style)
    lbl = Label(
        text=label,
        position=anchor,     # ← this is the final world-space position
        parent_id=eid,
        style=lbl_style,
    )
    self._scene.add_label(lbl)
```

The serializer outputs `position` as the final 3D world anchor. The `style` dict
carries `offset_2d` and `align` for the frontend.

---

## 8. Frontend Changes

### 8.1 Live Viewer (`viewer.js`)

```javascript
// In upsertObject(), for overlay labels with parentId:
if (msg.parentId) {
    css2d = new CSS2DObject(el);
    // No 3D offset — the position from Python is already the final anchor.
    // (parent-relative position is just the offset_local transformed).
    // Actually: since label is child of parent mesh, the anchor position
    // needs to be in parent-local space.
    // Simplification: the Python side computes the anchor relative to
    // the entity, passes it as `position`. The frontend doesn't need
    // the local frame — it just uses `position` relative to parent.
    const pos = msg.position || [0, 0, 0];
    css2d.position.set(pos[0], pos[1], pos[2]);
    
    // Apply 2D pixel offset
    const off2d = msg.style?.offset_2d || [0, 0];
    el.style.transform = `translate(${off2d[0]}px, ${off2d[1]}px)`;
    
    // Apply alignment
    const align = msg.style?.align || [0.5, 0.5];
    el.style.transform += ` translate(${-align[0] * 100}%, ${-align[1] * 100}%)`;
    
    parentObj.obj.add(css2d);
}
```

**Key insight:** Labels with `parentId` are children of the entity mesh, so their
`css2d.position` is relative to the parent. The Python side computes the anchor
**relative to the entity's origin** using the local frame. This means the
`position` sent over the wire is the **relative** position, not the absolute
world position.

For standalone labels (no `parentId`), the position is absolute world coordinates.

### 8.2 HTML Export (`_html.py`)

Same logic as the live viewer — use `msg.position` for the CSS2DObject position
(already relative to parent), and apply `offset_2d` and `align` via CSS transforms.

---

## 9. Computing Relative Position (Parent-Child)

When a label is attached to a parent entity, the CSS2DObject's position is
relative to the parent's origin. So the Python side must compute the anchor
**relative to the entity's center/origin**, not in world coordinates.

For a sphere at `(3, 0, 0)` with `offset_local=(0, 1.1, 0)`:
- `frame.origin` is the sphere center in world = `(3, 0, 0)`
- The local-frame offset is `(0, 1.1, 0)` scaled by radius 2 → `(0, 2.2, 0)`
- World anchor = `(3, 2.2, 0)`
- **Relative to entity origin** = `(0, 2.2, 0)`

That relative position `(0, 2.2, 0)` is what gets serialized as `position` for
parent-attached labels. The absolute world anchor is only used for standalone
labels.

### `compute_label_position()` — Parent-Relative

```python
def compute_label_position(entity, style: LabelStyle) -> tuple[float, float, float]:
    """Return the label anchor position relative to the entity's local origin.
    
    This is what gets serialized as ``position`` for parent-attached labels.
    """
    frame = get_label_frame(entity)
    ox, oy, oz = style.offset_local or (0.0, 0.0, 0.0)
    # The entity's origin is frame.origin, but we want position relative
    # to that origin.
    return (
        (ox * frame.x_axis[0] + oy * frame.y_axis[0] + oz * frame.z_axis[0]) * frame.scale,
        (ox * frame.x_axis[1] + oy * frame.y_axis[1] + oz * frame.z_axis[1]) * frame.scale,
        (ox * frame.x_axis[2] + oy * frame.y_axis[2] + oz * frame.z_axis[2]) * frame.scale,
    )
```

---

## 10. Serialized Label JSON

```json
{
  "id": "lbl_1",
  "layer": "overlay",
  "kind": "label",
  "text": "S1",
  "position": [0.0, 2.2, 0.0],
  "parentId": "sphere_1",
  "style": {
    "style_type": "LabelStyle",
    "font_size": 14,
    "font_family": "sans-serif",
    "color": "#ffffff",
    "background": "rgba(0, 0, 0, 0.6)",
    "offset_2d": [0, 0],
    "align": [0.5, 0.5]
  }
}
```

The `offset_local` is **not** sent to the frontend — it was already applied
when computing `position`. The frontend only needs `offset_2d` and `align`.

---

## 11. Files to Create / Modify

### 11.1 New Files

| File | Content |
|---|---|
| `py/pytanga/viz/_label_frame.py` | `LabelFrame` dataclass + `get_label_frame()` + `_perpendicular()`/`_cross()`/`_normalize()` helpers |

### 11.2 Modified Files

| File | Changes |
|---|---|
| `py/pytanga/viz/_styles.py` | `LabelStyle`: remove `offset`, `horizontal_alignment`, `vertical_alignment`; add `offset_local`, `offset_2d`, `align` |
| `py/pytanga/viz/_label.py` | `get_label_anchor()` returns pure geometry (no +0.3); add `compute_label_position()` |
| `py/pytanga/viz/visualizer.py` | `add()`: use `compute_label_position()` for label when `label=` is provided |
| `py/pytanga/viz/serializer.py` | `_serialize_label()`: serialize new LabelStyle fields |
| `py/pytanga/viz/templates/viewer.js` | Label positioning: use `msg.position` directly; apply `offset_2d` + `align` as CSS transforms |
| `py/pytanga/viz/export/_html.py` | Bootstrap adapter: same CSS transform logic for `offset_2d` + `align` |
| `py/tests/viz/test_phase4d_labels.py` | If it exists — update for new label positioning |
| `py/tests/viz/test_phase1_session_scene.py` | Update `test_defaults_include_label_keys` to check `offset_local`, `offset_2d`, `align` |

---

## 12. Implementation Checklist

### 12.1 `_label_frame.py` (new)

- [ ] **F1:** Create `LabelFrame` dataclass with `origin`, `x_axis`, `y_axis`, `z_axis`, `scale`
- [ ] **F2:** Implement `_normalize(vec)`, `_cross(a, b)`, `_length(vec)` helpers (pure Python, no numpy)
- [ ] **F3:** Implement `_perpendicular(direction)` — world axis with smallest dot
- [ ] **F4:** Implement `get_label_frame(entity) -> LabelFrame` for all 19 entity/operator kinds (see table §2.2)
- [ ] **F5:** Implement `compute_label_position(entity, style) -> tuple[float, float, float]` — offset_local in local frame, returns parent-relative position

### 12.2 `_styles.py` — LabelStyle Updates

- [ ] **S1:** Remove `offset` field (3-tuple)
- [ ] **S2:** Remove `horizontal_alignment` and `vertical_alignment` fields
- [ ] **S3:** Add `offset_local: tuple[float, float, float] | None = None`
- [ ] **S4:** Add `offset_2d: tuple[float, float] | None = None`
- [ ] **S5:** Add `align: tuple[float, float] | None = None`
- [ ] **S6:** Update `to_dict()` for new fields
- [ ] **S7:** Update `_DEFAULT_STYLE_FOR_KIND` entries — LabelStyle is not there, but the canonical `LabelStyle()` instance defaults to no offset, (0,0) 2D, (0.5,0.5) align

### 12.3 `_label.py` — Anchor & Position

- [ ] **L1:** Rewrite `get_label_anchor()` — no hardcoded margin offsets
- [ ] **L2:** Import and use `compute_label_position()` from `_label_frame.py`

### 12.4 `visualizer.py`

- [ ] **V1:** In `add()`, when `label="..."` is provided, use `compute_label_position()` with the appropriate style
- [ ] **V2:** Remove old `get_label_anchor` import path

### 12.5 `serializer.py`

- [ ] **Z1:** `_serialize_label()`: serialize new fields (`offset_2d`, `align`)

### 12.6 JS Frontend

- [ ] **J1:** `viewer.js` `upsertObject()`: use `msg.position` directly for CSS2DObject position
- [ ] **J2:** Apply `offset_2d` as CSS `translate(px, px)` on the label DOM element
- [ ] **J3:** Apply `align` as CSS `translate(-ax*100%, -ay*100%)` combined with offset_2d
- [ ] **J4:** `_html.py` bootstrap: same CSS transform logic

### 12.7 Tests

- [ ] **T1:** Test `LabelFrame` for all entity kinds (correct origin, axes orthonormal, correct scale)
- [ ] **T2:** Test `_perpendicular()` returns a unit vector perpendicular to input
- [ ] **T3:** Test `compute_label_position(Sphere(Point(0,0,0), 2), LabelStyle(offset_local=(0, 1.5, 0)))` → `(0, 3.0, 0)`
- [ ] **T4:** Test `compute_label_position(PointPair(Point(-2,0,0), Point(2,0,0)), LabelStyle(offset_local=(0, 1, 0)))` → local Y offset relative to midpoint
- [ ] **T5:** Test serialized label JSON contains `offset_2d` and `align` but **not** `offset_local`
- [ ] **T6:** All existing tests pass (84+)

### 12.8 Smoke / Manual

- [ ] **M1:** Labels appear at correct positions in live viewer (no regression)
- [ ] **M2:** Labels in HTML export match live viewer
- [ ] **M3:** `offset_2d` shifts label on screen in pixels
- [ ] **M4:** `align` correctly anchors label at edge/corner of the text box
- [ ] **M5:** No browser console errors

---

## 13. Summary of New API

### 13.1 Adding Labels

```python
from pytanga.viz import LabelStyle

# Default — label at entity center, no offset
viz.add(entity, label="S1")

# Custom label style — 10% above sphere top in local space, 5px right, 0px down
viz.add(
    entity,
    label="S1",
    label_style=LabelStyle(
        offset_local=(0.0, 1.1, 0.0),   # 10% above sphere surface
        offset_2d=(5.0, 0.0),             # 5px to the right
        align=(0.5, 1.0),                 # bottom-center of text at anchor
    ),
)
```

### 13.2 Configuring Default Label Style

```python
# Not via default_styles (labels aren't entity kinds) — 
# the LabelStyle default is the class-level default:
viz._default_label_style = LabelStyle(
    offset_local=(0.0, 1.1, 0.0),
    offset_2d=(0.0, 0.0),
    align=(0.5, 1.0),
)
```

(Exact API TBD — could be a `default_label_style` property on `Visualizer`.)

---

## 14. Verification Checklist

- [ ] `LabelFrame` computed for all 19 entity/operator kinds with orthonormal axes and correct scale
- [ ] `get_label_anchor()` returns pure geometry (no +0.3 additions)
- [ ] `compute_label_position()` returns parent-relative position (not world position)
- [ ] `LabelStyle` fields: `offset_local` (3D, local frame), `offset_2d` (2D px), `align` (2D 0-1)
- [ ] Old fields removed: `offset`, `horizontal_alignment`, `vertical_alignment`
- [ ] Serialized label JSON does NOT contain `offset_local`
- [ ] Serialized label JSON contains `offset_2d` and `align`
- [ ] Live viewer: labels positioned at correct world positions
- [ ] Live viewer: `offset_2d` and `align` applied as CSS transforms
- [ ] HTML export: labels match live viewer positions
- [ ] All existing tests pass
- [ ] No browser console errors