# Labels

Labels are text annotations rendered via Three.js CSS2DRenderer — crisp HTML
text that follows the entity in 3D space but always faces the camera.

See the example script [`basic.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/labels/basic.py)
for a runnable demonstration.

## Convenience Shortcut

```python
viz.add(Point(1, 2, 3), color="#ff4444", label="P₁")
```

This auto-creates a `Label` attached to the entity using the global default
`LabelStyle`. It returns the entity id as a `str`; the attached label ids are
available via `viz.get_label_ids(entity_id)` (a `list[str]`).

## `Label` Dataclass

```python
from pytanga.viz import Label

Label(
    text="S₁",                         # label text
    position=(0.0, 1.3, 0.0),         # 3D position (world or relative to parent)
    parent_id="sphere_1",              # optional: entity this label is attached to
    style=None,                        # optional LabelStyle
)
```

## `LabelStyle`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `font_size` | `float` | `14` | CSS font-size in px |
| `font_family` | `str` | `"sans-serif"` | CSS font-family |
| `color` | `str` | `"#ffffff"` | Text color |
| `background` | `str` | `"rgba(0,0,0,0.6)"` | CSS background |
| `font_weight` | `str \| None` | `None` | `"bold"`, `"normal"` |
| `text_transform` | `str \| None` | `None` | `"uppercase"`, `"none"` |
| `offset_local` | `(float, float, float)` | `(0, 0, 0)` | 3D offset in the entity's local frame, scaled by entity size |
| `offset_2d` | `(float, float)` | `(0, 0)` | 2D screen-space pixel offset after projection |
| `align` | `(float, float)` | `(0.5, 0.5)` | Alignment: `(0,0)` = top-left, `(1,1)` = bottom-right |
| `along` | `float \| (float, float) \| (float, float, float)` | `None` | Anchor fraction(s) along the entity's extent; line default `0.5` = midpoint |
| `rotation` | `float` | `0` | Screen-plane rotation in degrees about the anchor (clockwise) |

## Label Positioning

The label anchor is computed from entity geometry (sphere top, point pair
midpoint, etc.) with no hardcoded margin. The `offset_local` is applied in
the entity's **local coordinate system** and **scaled by the entity's
characteristic size**:

| Entity | Scale | Local Y direction |
|--------|-------|-------------------|
| Sphere | radius | world up |
| Line | rendered length | perpendicular to direction |
| Plane | extent | plane normal |
| Point | 1.0 | world up |

```
For a sphere at (3, 0, 0) with radius 2:
  offset_local = (0, 0.0, 0)  →  label at sphere center
  offset_local = (0, 1.0, 0)  →  label at sphere surface (2 × 1.0 = 2 units up)
  offset_local = (0, 1.1, 0)  →  label slightly above surface (10% gap)
```

After the 3D position is projected to screen space, `offset_2d` shifts the
label in pixels, and `align` controls how the text box is positioned relative
to the anchor point.

### Per-entity anchors (`along`)

`along` parameterizes where along an entity's extent the label anchors,
as a scalar or a 2-/3-tuple of fractions:

| Entity | dim | meaning | default |
|--------|-----|---------|---------|
| Line | 1 | fraction along the segment (`0` = origin, `1` = end) | `0.5` (midpoint) |
| Direction | 1 | fraction along the arrow | `0` |
| PointPair | 1 | fraction A→B | `0.5` |
| Plane | 2 | fractions along the two in-plane axes | `(0, 0)` = reference point |
| Circle | 2 | radius fraction, angle fraction (× π) | `(0, 0)` = centre |
| Sphere | 3 | radius fraction, two angle fractions (× π) | `(0, 0, 0)` = centre |

```python
viz.add(Line.from_points(Point(0, 0, 0), Point(4, 0, 0)), label="mid")   # 0.5
viz.styles.label_kind["Line"].along = 1.0                              # at the end
```

### Screen-plane rotation (`rotation`)

`rotation` (degrees, clockwise) rotates the label about its final anchor in
the screen plane — useful for coordinate-axis tick labels so longer labels
don't overlap:

```python
viz.styles.label_kind["Axis"] = LabelStyle(rotation=-45)
```

## Default Label Styling

```python
from pytanga.geometry import Sphere

# Global default — affects all labels
viz.styles.label_base.offset_local = (0.0, 1.1, 0.0)
viz.styles.label_base.align = (0.5, 1.0)

# Per-kind override — only for Sphere labels
viz.styles.label_kind["Sphere"] = LabelStyle(offset_local=(0.0, 1.05, 0.0))
```

Priority: user's `label_style` > per-kind default > global default.

## Standalone Labels

```python
from pytanga.viz import Label, LabelStyle

# Attached to an existing entity
eid = viz.add(Sphere(Point(5, 0, 0), 1.0))
viz.add(Label(text="My Sphere", position=(0, 1.3, 0), parent_id=eid))

# Absolute world position, no parent
viz.add(Label(text="Origin", position=(0, 0, 0)))
```

## Updating Labels

```python
# Change text and/or style without repositioning
viz.update_label(label_id, text="Updated", style=LabelStyle(color="#ff0"))

# Remove label
viz.update_label(label_id, text="")
```

## KaTeX Math in Labels

Label text containing `$...$` delimiters is automatically rendered as
LaTeX math using KaTeX. Both inline (`$...$`) and display (`$$...$$`) math
are supported:

```python
viz.add(Point(1, 2, 3), label="$\\mathbf{P}_1$")
viz.add(Sphere(Point(0, 0, 0), 2.5), label="$S_1$")
viz.add(Point(0, 0, 0), label="Origin: $\\vec{0}$")
```

KaTeX rendering works in the live viewer and in all HTML export formats
(static, figure, and animated).