# Labels

Labels are text annotations rendered via Three.js CSS2DRenderer — crisp HTML
text that follows the entity in 3D space but always faces the camera.

See the example script [`demo_labels.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_labels.py)
for a runnable demonstration.

## Convenience Shortcut

```python
viz.add(Point(1, 2, 3), color="#ff4444", label="P₁")
```

This auto-creates a `Label` attached to the entity using the global default
`LabelStyle`. Returns `(entity_id, label_id)` as a 2-tuple.

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

## Default Label Styling

```python
from pytanga.geometry import Sphere

# Global default — affects all labels
viz.default_label_style.offset_local = (0.0, 1.1, 0.0)
viz.default_label_style.align = (0.5, 1.0)

# Per-kind override — only for Sphere labels
viz.default_label_styles["Sphere"] = LabelStyle(offset_local=(0.0, 1.05, 0.0))
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