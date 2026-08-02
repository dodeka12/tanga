# Style System

Each geometric entity and operator kind has a dedicated **style dataclass**
that controls its visual appearance. All style fields default to `None` —
the `Visualizer` stores fully-initialized canonical defaults that fill any
unset fields.

See the example script [`demo_custom_defaults.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_custom_defaults.py)
for a runnable demonstration.

## Setting Defaults

```python
from pytanga.viz import LineStyle, SphereStyle
from pytanga.geometry import Sphere

# Mutate canonical defaults via class-based access (autocomplete-friendly)
viz.default_styles[Sphere].wireframe = False
viz.default_styles[Sphere].opacity = 0.6

# Or via string keys
viz.default_styles["Line"] = LineStyle(length=30.0, thickness=0.05)

# Quick color-only override (also supports RGBA tuples for opacity)
viz.set_default_color("point", "#00ff00")
viz.set_default_color("sphere", (0.0, 0.0, 1.0, 0.5))  # blue + 50% opacity
```

The `default_styles` property supports both **class-based access**
(`viz.default_styles[Sphere]`) and **string-based access**
(`viz.default_styles["Sphere"]`).

## Per-Call Style Overrides

```python
from pytanga.viz import SphereStyle, PointStyle

# Override only specific style fields — the rest come from canonical defaults
viz.add(Point(1, 2, 3), style=PointStyle(size=0.2))
viz.add(Sphere(Point(0, 0, 0), 2), style=SphereStyle(wireframe=False))

# Shortcut kwargs for color/opacity (highest priority)
viz.add(Point(1, 2, 3), color="#ff0", opacity=0.8, style=PointStyle(size=0.2))
```

**Priority:** `add(color=...)` > `style=SphereStyle(color=…)` > `default_styles[Sphere]`

## All Style Classes

| Style | For | Fields |
|-------|-----|--------|
| `PointStyle` | `Point` | `color`, `opacity`, `size` |
| `DirectionStyle` | `Direction` | `color`, `opacity`, `length` |
| `HPointStyle` | `HPoint` | `color`, `opacity`, `size` |
| `PointPairStyle` | `PointPair`, `ImagPointPair` | `color`, `opacity`, `point_size`, `line_thickness`, `wireframe`, `wireframe_dash`, `wireframe_color`, `wireframe_opacity` |
| `LineStyle` | `Line` | `color`, `opacity`, `length`, `thickness`, `wireframe`, `wireframe_dash`, `wireframe_color`, `wireframe_opacity` |
| `PlaneStyle` | `Plane` | `color`, `opacity`, `extent`, `wireframe`, `wireframe_dash`, `wireframe_color`, `wireframe_opacity` |
| `CircleStyle` | `Circle`, `ImagCircle` | `color`, `opacity`, `tube_radius`, `wireframe`, `wireframe_dash`, `wireframe_color`, `wireframe_opacity` |
| `SphereStyle` | `Sphere`, `ImagSphere` | `color`, `opacity`, `wireframe`, `wireframe_dash`, `wireframe_color`, `wireframe_opacity` |
| `SpaceStyle` | `Space` | `color`, `opacity`, `extent` |
| `ReflectionLineStyle` | `ReflectionLine` | `color`, `opacity`, `length`, `thickness` |
| `ReflectionPlaneStyle` | `ReflectionPlane` | `color`, `opacity`, `extent` |
| `ReflectionOriginStyle` | `ReflectionOrigin` | `color`, `opacity`, `extent` |
| `InversionStyle` | `Inversion` | `color`, `opacity` |
| `RotorStyle` | `Rotor` | `color`, `opacity`, `disc_radius` |
| `TranslatorStyle` | `Translator` | `color`, `opacity`, `length` |
| `DilatorStyle` | `Dilator` | `color`, `opacity`, `ring_count`, `max_radius` |
| `MotorStyle` | `Motor` | `color`, `opacity` |
| `GeneralRotorStyle` | `GeneralRotor` | `color`, `opacity` |
| `GeneralDilatorStyle` | `GeneralDilator` | `color`, `opacity`, `ring_count`, `max_radius` |
| `FigureStyle` | figure export | `width`, `height`, `background`, `auto_rotate`, `show_grid`, `show_axes`, `show_title`, `show_annotation`, `border_radius`, `responsive` |
| `AnimStyle` | animated export | `fps`, `loop`, `show_controls`, `compress` |

See [Export & Capture](export.md) for `FigureStyle` and `AnimStyle` defaults
and usage.

## Default Colors

| Kind | Default Color |
|------|---------------|
| Point | `#ff4444` (red) |
| Direction | `#ffffff` (white) |
| HPoint | `#ff8844` (orange) |
| PointPair | `#44ff44` (green) |
| Line | `#44ff44` (green) |
| Plane | `#4488ff` (blue) |
| Circle | `#ff44ff` (magenta) |
| Sphere | `#ffaa00` (amber) |
| Space | `#888888` (grey) |
| ReflectionLine | `#aaccff` (light blue) |
| ReflectionPlane | `#88ccff` (light blue) |
| ReflectionOrigin | `#ffffff` (white) |
| Inversion | `#cc88ff` (lavender) |
| Rotor | `#ff8844` (orange) |
| Translator | `#44aaff` (blue) |
| Dilator | `#ffcc44` (amber) |
| Motor | `#ff66cc` (pink) |
| GeneralRotor | `#ff9966` (salmon) |
| GeneralDilator | `#ffcc88` (peach) |
| ImagPointPair | `#ff88ff` (pink) |
| ImagCircle | `#ff88ff` (pink) |
| ImagSphere | `#ff8844` (orange) |

## Wireframe & Dash Patterns

`LineStyle`, `PlaneStyle`, `CircleStyle`, `SphereStyle`, and `PointPairStyle`
all support wireframe rendering via these fields:

| Field | Type | Description |
|-------|------|-------------|
| `wireframe` | `bool` | When ``True``, a wireframe cage is drawn over the solid surface. ``SphereStyle`` defaults to ``True``. |
| `wireframe_dash` | `WireframeDashPattern` | Dash pattern — ``None`` defaults to solid lines. |
| `wireframe_color` | `str` | Optional override color for wireframe lines (``None`` = entity color). |
| `wireframe_opacity` | `float` | Opacity of wireframe lines (0–1, ``None`` = fully opaque). |

### Dash Pattern Classes

| Class | Dash size | Gap size | Visual |
|-------|-----------|----------|--------|
| `SolidWireframe` | 0 | — | Unbroken line |
| `DashedWireframe` | 0.005 | 0.003 | Standard dashes |
| `DottedWireframe` | 0.0015 | 0.005 | Dotted pattern |

```python
from pytanga.viz import DashedWireframe, DottedWireframe, SolidWireframe

viz.add(Sphere(0, 0, 0, 2), style=SphereStyle(
    wireframe=True,
    wireframe_dash=DashedWireframe(),
    wireframe_color="#00ffff",
    wireframe_opacity=0.5,
))

viz.add(Plane(Point(0, 0, 0), Direction(0, 0, 1)), style=PlaneStyle(
    wireframe=True,
    wireframe_dash=DottedWireframe(),
))
```

## Imaginary Entity Defaults

`ImagCircle`, `ImagSphere`, and `ImagPointPair` have distinct canonical
defaults that differ from their real counterparts:

| Kind | Default Style |
|------|---------------|
| `ImagCircle` | `wireframe=True`, `wireframe_dash=DottedWireframe()`, `opacity=0.0` (fully transparent surface, wireframe-only) |
| `ImagSphere` | `wireframe=True`, `wireframe_dash=DottedWireframe()`, `wireframe_opacity=0.6`, `opacity=0.3` |
| `ImagPointPair` | `wireframe=True`, `wireframe_dash=DottedWireframe()`, `wireframe_opacity=0.6`, `color=#ff88ff` |

Override them via class-based access:

```python
from pytanga.viz import DashedWireframe
from pytanga.geometry import ImagCircle

viz.default_styles[ImagCircle].wireframe_dash = DashedWireframe()
viz.default_styles[ImagCircle].opacity = 0.2
```

## Extended Styles — `CrossHairPointStyle`

`CrossHairPointStyle(PointStyle)` renders a 3D crosshair (three orthogonal
cylinders) instead of a sphere, while inheriting `color`, `opacity`, and
`size` from the `PointStyle` base class.

```python
from pytanga.viz import CrossHairPointStyle

# Crosshair with defaults (color/opacity from canonical PointStyle)
viz.add(Point(1, 2, 3), style=CrossHairPointStyle())

# Crosshair with explicit overrides
viz.add(Point(5, 0, 0), style=CrossHairPointStyle(
    color="#00ff00", opacity=0.8, size=0.5, arm_thickness=0.05
))
```

This is the reference pattern for future extended styles — inherit from the
base `*Style`, add new fields (all defaulting to `None`), override `to_dict()`,
and add a new JS renderer module dispatched on the `style_type` string.